import pandas as pd
import numpy
import numpy.ma
import pickle
import math
from functools import partial
from pyairtable import Table

def load_tables(table_names,api_key,base_id,cache=False):
    """
    Loads all tables in table_names from Airtables, sorts them by index, which is set to the "Date" column,
    then merges them and return as one Bokeh ColumnDataSource.
    """
    if not cache:
        tables = []
        for tn in table_names:
            table = Table(api_key, base_id,tn)
            print(tn)
            df = convert_to_dataframe(table.all(),index_column="Date",datatime_index=True)
            df.sort_index(inplace=True)
            df.drop(df.index[:1], inplace=True)
            tables.append(df)

        # check for duplicates
        for t,tn in zip(tables,table_names):
            print('There are following duplicates in table ' + tn + " :" + str(t.index[t.index.duplicated()]))

        df = pd.concat(tables,axis=1,join='outer')
        


        # check if no days are missing 
        for i in range(0,len(df.index)-1):
            assert (df.index[i] + pd.offsets.Day()) == df.index[i+1], "Error, no gaps in data allowed. The following consecutive data points are not a day apart: %s %s" % (str(df.index[i]),str(df.index[i+1]))

        # let's load up the metadata
        metadata_table = Table(api_key, base_id,'Metadata')
        md = convert_to_dataframe(metadata_table.all(),index_column="Name")
        md['Start of valid records'] = pd.to_datetime(md['Start of valid records'])
        md['Ignore'] = numpy.nan_to_num(pd.to_numeric(md['Ignore']))

        # convert bool columns to float
        for col in df.columns:
            if md['Units'].loc[col] == 'bool':
                df[col] = pd.to_numeric(df[col])

        # convert enum columns to numbers
        for col in df.columns:
             if md['Units'].loc[col] == 'enum':
                d = set(df[col].tolist())
                d = {j:i for i,j in enumerate(d)}

                def enum_to_int(r,d):
                    if r != r:
                        return r
                    else:
                        return d[r]

                df[col] = df[col].apply(partial(enum_to_int,d=d))                 
                
        # convert hh:mm to interger representing the number of minutes from midnight
        # FOR NOW ALL SUCH FIELDS ARE USED AS DURATION FIELD IN AIRTABLES WHICH STORES THEM AS SECONDS 
        # for col in df.columns:
        #     if md['Units'].loc[col] == 'hh:mm':
        #        def hhmm_to_min(s):
        #            print(s)
        #            if s != None and s == s: # second test is for NAN, NAN != NAN
        #                 assert type(s) == str, "%s in column %s doesn't follow hh:mm format" % (s,col)
        #                 assert len(s) <= 5, "%s in column %s doesn't follow hh:mm format" % (s,col)
        #                 assert s[0] in ['0','1','2','3','4','5','6','7','8','9'] , "%s in column %s doesn't follow hh:mm format" % (s,col)
        #                 flag = False
        #                 for c in s[1:]:
        #                     if c == ':' and flag:
        #                        assert False , "%s in column %s doesn't follow hh:mm format" % (s,col)
        #                     if c == ':':
        #                         flag = True
        #                     else:
        #                        assert c in ['0','1','2','3','4','5','6','7','8','9'] , "%s in column %s  doesn't follow hh:mm format" % (s,col)
        #                 if not flag:
        #                    assert False , "%s in column %s doesn't follow hh:mm format" % (s,col)
        #                 s = int(s.split(":")[0])*60+int(s.split(":")[1])
        #            return s
        #        df[col] = df[col].apply(hhmm_to_min)

        # Sometimes airtable puts NaNs into tables in the form {'specialValue' : NaN}. This replaces those with just NaN
        for col in df.columns:
            def nandict_to_nan(s):
                if isinstance(s,dict):
                    return numpy.nan
                else:
                    return s
            df[col] = df[col].apply(nandict_to_nan)

        # remove columns that are strings or to be ignored
        to_be_droped=[]
        for col in df.columns:
            if md['Units'].loc[col] == 'string' or md['Ignore'].loc[col]==1:
               to_be_droped.append(col)
        
        print("Number of columns before cleaning:" + str(len(df.columns)))
        df = df.drop(to_be_droped,axis=1)
        print("Number of columns after cleaning:" + str(len(df.columns)))
        
        # replace NaN with default values if they are specified, but only after 'Start of valid records'
        for col in df.columns:
            if md['Units'].loc[col] != 'string':
                df[col] = numpy.nan_to_num(df[col].to_numpy(float,na_value=numpy.nan),md['Default'].loc[col]) if not math.isnan(md['Default'].loc[col]) else df[col].to_numpy(float,na_value=numpy.nan)
                if not pd.isnull(md['Start of valid records'].loc[col]):
                   df.loc[:md['Start of valid records'].loc[col],col] = numpy.nan
                if not pd.isnull(md['End of valid records'].loc[col]):
                   df.loc[md['End of valid records'].loc[col]:,col] = numpy.nan

        # cache the data
        pickle.dump((df,md),open('./locals/cache.pickle','bw'))
    else:
        (df,md) = pickle.load(open('./locals/cache.pickle','br'))
        
    # let's populate categories 
    categories = {}
    for category in table_names:
        categories[category] = [i for i in md.loc[md['Category'] == category].index.tolist() if i in df.columns]

    return df,md,categories

#def load_PANAS_tables(api_key,base_id):
#    tables = []
#    for tn in ['PANAS20morning','PANAS20lunchtime','PANAS20afternoon','PANAS20evening']:
#            df = convert_to_dataframe(airtable_download(tn,api_key=api_key,base_id=base_id),index_column="Date",datatime_index=True)
#            df.sort_index(inplace=True)
#            df.drop(df.index[:1], inplace=True)
#            tables.append(df)
#
#    pe = sum([df['Positive Effects'] for df in tables])/4
#    ne = sum([df['Negative Effects'] for df in tables])/4

def load_blood_tests(api_key,base_id,cache=False):
    table = Table(api_key, base_id, 'BloodTest')

    views = {
        "WBC Rest" : ["Leukocites (G/L)", "RBC (T/L)", "Hemoglobin (g/L)", "Hematocrite ()", "MCV (fl)", "MCH  (pg)", "MCHC (g/dl)","Palettel (G/L)", "Palettel Distribution Width (%)", "RBC Distribution Width CV (%)", "MPV (fl)", "ESR (mm/h)", "Protrombin_time (s)", "Protrombin_time_R", "Protrombin_time_INR", "APTT-P (s)", "APTT_R", "Fibrinogen (g/l)", "Thrombin time (s)", "Antitrombin (%)", "D-dimer (mg/l)"],
        "WBC Differential" : ["Neutrophiles (%)", "Lymfocytes (%)", "Monocytes  (%)", "Esophiles  (%)", "Basophiles (%)", "Lymphocyte count (G/l)", "Monocytes count (G/l)", "Neutrophils count (G/l)", "Esophiles clount (G/l)", "Basophiles count (G/l)", "Neutrophils/Lymphocytes ()", "Retikulocity (%)", "Retikulocytes count (10^9/l)", "NRBC count"],
        "Immunity" : ["CRP (mg/l)", "IG (g/l)", "IgA (g/l)", "IgM (g/l)", "IgE (IU/l)", "Rheumatoid Factor (kU/l)", "IL 6 (ng/l)"],
        "Minerals" : ["Na (mEq/L)", "K (mEq/L)", "Cl (mmol/l)", "Ca (mmol/l)", "Ca(corig) (mmol/l)", "Fe (mumol/l)", "Mg (mmol/l)", "P (mmol/l)", "Cu (μmol/L)"],
        "Kidney Function" : ["Urea (mmol/L)", "Kreatinin  (μmol/l)", "GFR (CKD-EPI) (ml/s/1.73 m2)", "eGFR (Lund-Malmo) (ml/s/1.73 m2)", "Uric acid (μmol/l)", "Cystain C (mg/l)", "GF Cystain C (ml/s/1,73 m2)"],
        "Liver Function" : ["Bilirubin (overall) (µmol/l)", "Bilirubin (conjugated) (µmol/l)", "ALT (μkat/l)", "AST (μkat/l)", "GGT (μkat/l)", "ALP (μkat/l)"],
        "Pancreas" : ["Amylase pancreatic (blood) (μkat/l)", "Amalyse", "Lipase (μkat/l)"],
        "Proteins" : ["Proteins (g/L)", "Ablumin (g/L)", "Ferritin (ug/L)"],
        "Cardio" : ["Troponin_hs (ng/l)", "LP-PLA2 (U/I)"],
        "Glucose" : ["Fasting Glucose (mmol/l)", "HOMA-IR ()", "QUICKI ()", "HbA1c (mmol/mol)"],
        "Iron metabolism" : ["Fe (mumol/l)", "Ferritin (ug/L)", "TIBC (umol/l)", "UIBC", "Transferin (g/l)", "TRF saturation (%)"],
        "Lipids" : ["Cholesterol (mmol/l)", "LDL (mmol/l)", "HDL (mmol/l)", "Tryglicerides (mmol/l)", "Non-HDL cholesterol (mmol/l)", "Chol/HDL ()", "Tryg/HDL ()", "Apolipoprotein A1 (g/L)", "Apolipoprotein B (g/L)", "Lp(a) (g/L)", "Lp(a) (nmol/l)"],
        "Thyroid" : ["TSH (mU/l)", "free-T4 (pmol/l)"],
        "Hormones" : ["Insulin (mlU/l)", "IGF-1 (µg/l)", "estradiol (pmol/l)", "testosterone (nmol/l)", "Cortisol (nmol/l)", "DHEAS (μmol/l)"],
        "Vitamins" : ["Homocystein (µmol/l)", "Vitamin D (nmol/l)", "Folate (nmol/l)", "B12 (pmol/l)"],
        "Prostate" : ["Total PSA (µg/l)", "Free PSA  (µg/l)", "FPSA/PSA ()"],
        "BiologicalAgeScores" : ["PhenoAge", "Aging AI 3.0", "YoungAI"],
        "Inflammation" : ["CRP (mg/l)", "LDH (ukat/l)"],
        "Cancer" : ["Total PSA (µg/l)", "Free PSA  (µg/l)", "AFP (ug/l)", "Free beta-HCG (ng/ml)"],
        "PhenoAge" : ["Leukocites (G/L)", "MCV (fl)", "RBC Distribution Width CV (%)", "Lymfocytes (%)", "CRP (mg/l)", "Kreatinin  (μmol/l)", "ALP (μkat/l)", "Ablumin (g/L)", "Fasting Glucose (mmol/l)"]        
    }

    if not cache:
        blood_tests = {}
        for view in views:
            blood_tests[view] = convert_to_dataframe(table.all(fields = views[view]+["Date"]),index_column="Date", datatime_index=True)
            blood_tests[view].sort_index(inplace=True)
            print(blood_tests[view].columns)
            
        # cache the data
        pickle.dump(blood_tests,open('./locals/cache_bt.pickle','bw'))
    else:
        blood_tests = pickle.load(open('./locals/cache_bt.pickle','br'))

    return blood_tests



def filter_data(type,data,sig):
    def gaussian(x, sig,mu):
        return numpy.exp(-numpy.power(x-mu, 2.) / (2 * numpy.power(sig, 2.)))

    def past_gaussian(x, sig,mu):
        r = numpy.exp(-numpy.power(x-mu, 2.) / (2 * numpy.power(sig, 2.)))
        return numpy.where((x-mu)<=0,r,numpy.zeros(len(x)))

    def future_gaussian(x, sig,mu):
        r = numpy.exp(-numpy.power(x-mu, 2.) / (2 * numpy.power(sig, 2.)))
        return numpy.where((x-mu)>=0,r,numpy.zeros(len(x)))

    if type == 'Gauss':
       fff = gaussian
    elif type == 'PastGauss':
       fff = past_gaussian
    elif type == 'FutureGauss':
       fff = future_gaussian

    ls = numpy.array(range(0,len(data)))
    filtr = fff(ls,sig,int(len(data)/2))

    d = numpy.ma.masked_invalid(data)

    result = numpy.array([numpy.ma.average(d,weights=fff(ls,sig,i)) for i in ls])
    return filtr,result


def data_aquisition_overlap(data1,data2):
   
    if len(numpy.argwhere(numpy.logical_not(numpy.isnan(numpy.array(data2))))) == 0 or len(numpy.argwhere(numpy.logical_not(numpy.isnan(numpy.array(data1))))) == 0:
       return 0,0

    start = int(max(numpy.argwhere(numpy.logical_not(numpy.isnan(numpy.array(data1))))[0][0],numpy.argwhere(numpy.logical_not(numpy.isnan(numpy.array(data2))))[0][0]))
    end = int(min(numpy.argwhere(numpy.logical_not(numpy.isnan(numpy.array(data1))))[-1][0],numpy.argwhere(numpy.logical_not(numpy.isnan(numpy.array(data2))))[-1][0]))
    return start,end

def data_aquisition_overlap_non_nans(data1,data2):
    start,end  = data_aquisition_overlap(data1,data2)
    idx = numpy.logical_not(numpy.logical_or(numpy.isnan(numpy.array(data1)),numpy.isnan(numpy.array(data2))))[start:end]
    return data1[start:end][idx],data2[start:end][idx]


def cross_corr(data1,data2,filtered_data1,filtered_data2):
    start, end = data_aquisition_overlap(data1,data2)
    if start < end:
        # we want to have symmetric output of cross-correlation where middle point is correlation of unshifted data
        if (end-start) % 2 == 0:
           end=end-1
        cc = numpy.correlate(filtered_data1[start:end]-numpy.mean(filtered_data1[start:end]),filtered_data2[start:end]-numpy.mean(filtered_data2[start:end]),mode='same') / numpy.sqrt(numpy.sum(numpy.power(filtered_data1[start:end]-numpy.mean(filtered_data1[start:end]),2)) * numpy.sum(numpy.power(filtered_data2[start:end]-numpy.mean(filtered_data2[start:end]),2)))
        return (cc,numpy.array(range(-int(len(cc)/2),int(len(cc)/2+1))))
    else:
       return None

def both_valid(data1,data2):
    select = numpy.logical_not(numpy.logical_or(numpy.isnan(data1),numpy.isnan(data2)))
    return data1[select],data2[select]


def event_weighted_average(a,b):
    """
    Takes two vectors a,b with of equal length L. 
    For each value A in vector a it selects a window W of length L from b centered on the same location as A (filled
    with zeros where the window goes beyond borders of b).
    
    It returns the mean of A*W across all non NaN values in a.
    
    NaN values in B are ignored when calculating the mean.  
    """
    half_length =  int(numpy.floor(len(a)/2))
    mb = numpy.mean(b)

    c = numpy.concatenate([[float('NaN')]*half_length,b,[float('NaN')]*half_length])
    d = []
    for i in range(0,len(a)):
        if not numpy.isnan(a[i]):
            d.append(a[i]*c[i:i+half_length*2+1])
    return numpy.nanmean(numpy.array(d),axis=0)/numpy.nanmean(a)

def event_triggered_change(veca,vecb,w,default=0):
    """
    Takes two vectors a,b of equal length. Both can have NaNs.
    
    For each non-default non-NaN value at position I in vector a:
     * M1 is the average of w values in b before index I 
     * M2 is the average of w values in b after index I 
     * add tuple M1,M2 to list L
    
    Run wilcoxon signed rank test on the resulting pairs and return in PVAL the p-value.
    
    Returns L,PVAL
    """
    
    res = []
    
    for i,v in enumerate(veca):
        if (not numpy.isnan(v)) and (v != default):
           if not numpy.isnan(numpy.nanmean(vecb[i-w:i])) and not numpy.isnan(numpy.nanmean(vecb[i:i+w])):
               res.append((numpy.nanmean(vecb[i-w:i]),numpy.nanmean(vecb[i:i+w]))) 
        
        from scipy.stats import wilcoxon
        
    c,d = zip(*res)
    stat, pvalue = wilcoxon(c,d)

    return res, stat, pvalue

categories = {}

def convert_to_dataframe(airtable_records,index_column=None,datatime_index=False):
    """Converts dictionary output from airtable_download() into a Pandas dataframe."""
    airtable_rows = []
    airtable_index = []
    for record in airtable_records:
        if index_column != None:
            if datatime_index:
                 airtable_index.append(pd.to_datetime(record['fields'][index_column]))
            else:
                airtable_index.append(record['fields'][index_column])
            record['fields'].pop(index_column)
        else:
            airtable_index.append(record['id'])
        airtable_rows.append(record['fields'])
        
    airtable_dataframe = pd.DataFrame(airtable_rows, index=airtable_index)
    return airtable_dataframe
