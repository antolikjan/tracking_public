from functools import partial
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Row, Column, Button, TableColumn, DataTable, Spacer, Slider, RadioButtonGroup, Select, DatePicker, Paragraph, Div, MultiChoice, HTMLTemplateFormatter, Paragraph, TabPanel
import scipy.stats
import numpy
import scripts.create_app
import scripts.comparison
from datetime import datetime
from datetime import date
from scipy.signal import lfilter

numpy.set_printoptions(threshold=numpy.inf)

ui = {}

val1 = []
val2 = []
rs = []
pvals = []
shift = []

rs_v1_pr_v2 = []
rs_v2_pr_v1 = []
rs_nosh = []
pvals_v1_pr_v2 = []
pvals_v2_pr_v1 = []
pvals_nosh = []

acc_p = []
acc_r = []
acc_dir = []
acc_sigma = []


data_table = None

def past_gauss_filter_matrix(data,sig):
    data = numpy.asarray(data,dtype=float)
    kernel = numpy.exp(-numpy.power(numpy.arange(data.shape[0]),2.0)/(2*numpy.power(sig,2)))
    valid = numpy.isfinite(data).astype(float)
    filled = numpy.nan_to_num(data,nan=0.0)

    numerator = lfilter(kernel,[1.0],filled,axis=0)
    denominator = lfilter(kernel,[1.0],valid,axis=0)
    result = numpy.full(data.shape,numpy.nan)
    numpy.divide(numerator,denominator,out=result,where=denominator != 0)
    return result

def exclude_last_valid_observation(data):
    result = numpy.array(data,dtype=float,copy=True)
    valid = numpy.isfinite(result)
    for col in range(result.shape[1]):
        valid_indices = numpy.flatnonzero(valid[:,col])
        if len(valid_indices) > 0:
            result[valid_indices[-1],col] = numpy.nan
    return result

def pairwise_regression_stats(data1,data2,min_count,var_tol):
    data1 = exclude_last_valid_observation(data1)
    data2 = exclude_last_valid_observation(data2)

    valid1 = numpy.isfinite(data1).astype(float)
    valid2 = numpy.isfinite(data2).astype(float)
    filled1 = numpy.nan_to_num(data1,nan=0.0)
    filled2 = numpy.nan_to_num(data2,nan=0.0)

    count = valid1.T @ valid2
    sum1 = filled1.T @ valid2
    sum2 = valid1.T @ filled2
    sum1_sq = numpy.square(filled1).T @ valid2
    sum2_sq = valid1.T @ numpy.square(filled2)
    sum12 = filled1.T @ filled2

    r = numpy.full(count.shape,numpy.nan)
    p = numpy.full(count.shape,numpy.nan)
    valid_count = count > min_count

    with numpy.errstate(invalid='ignore',divide='ignore'):
        ss1 = sum1_sq - numpy.square(sum1) / count
        ss2 = sum2_sq - numpy.square(sum2) / count
        covariance = sum12 - (sum1 * sum2) / count
        valid = numpy.logical_and(valid_count,numpy.logical_and(ss1 > var_tol,ss2 > var_tol))
        numpy.divide(covariance,numpy.sqrt(ss1 * ss2),out=r,where=valid)
        r = numpy.clip(r,-1.0,1.0)
        degrees_of_freedom = count - 2
        t_stat = r * numpy.sqrt(degrees_of_freedom / (1 - numpy.square(r)))
        p_values = 2 * scipy.stats.t.sf(numpy.abs(t_stat),degrees_of_freedom)

    p[valid] = p_values[valid]
    p[numpy.logical_and(valid,numpy.abs(r) == 1.0)] = 0.0
    return r,p

def correlation_analysis(data,metadata,source,relationships):
    val1.clear()
    val2.clear()
    rs.clear()
    pvals.clear()
    shift.clear()

    rs_v1_pr_v2.clear()
    rs_v2_pr_v1.clear()
    rs_nosh.clear()
    pvals_v1_pr_v2.clear()
    pvals_v2_pr_v1.clear()
    pvals_nosh.clear()

    acc_p.clear()
    acc_r.clear()
    acc_dir.clear()
    acc_sigma.clear()


    cols = list(data.columns)    
    print("Number of columns in the dataset: " + str(len(cols)))

    selected_range = numpy.logical_and(data.index >= datetime.strptime(ui['dt_pckr_start'].value,"%Y-%m-%d"),data.index <= datetime.strptime(ui['dt_pckr_end'].value,"%Y-%m-%d")) 
    #prepare the convolved data
    sigmas = [2,4,8,16,32,64,128,256]
    convolved = []
    selected_data = data.loc[selected_range,:].to_numpy(float)
    for s in sigmas:
        convolved.append(past_gauss_filter_matrix(selected_data,s))

    r_nosh,p_nosh = pairwise_regression_stats(selected_data,selected_data,20,0.0)
    r_v2_pr_v1,p_v2_pr_v1 = pairwise_regression_stats(selected_data[1:,:],selected_data[:-1,:],20,0.0)
    r_v1_pr_v2,p_v1_pr_v2 = pairwise_regression_stats(selected_data[:-1,:],selected_data[1:,:],20,0.0)
    accumulation_stats = [
        pairwise_regression_stats(convolved_data,selected_data,4,0.00000000000000001)
        for convolved_data in convolved
    ]

    for i in range(len(cols)):
        for j in range(i+1,len(cols)): 

            # make sure both variables are numeric
            if metadata['Units'].loc[cols[i]] != 'string' and metadata['Units'].loc[cols[j]] != 'string':

                    res1 = None if numpy.isnan(p_nosh[i,j]) else (r_nosh[i,j],p_nosh[i,j])
                    res2 = None if numpy.isnan(p_v2_pr_v1[i,j]) else (r_v2_pr_v1[i,j],p_v2_pr_v1[i,j])
                    res3 = None if numpy.isnan(p_v1_pr_v2[i,j]) else (r_v1_pr_v2[i,j],p_v1_pr_v2[i,j])

                    res = None                       
                    if res1 != None and (res2 == None or res1[1] < res2[1]) and (res3 == None or res1[1] < res3[1]):
                       res = res1
                       shi = '=='
                    elif res2 != None and (res3 == None or res2[1] < res3[1]):  
                       res = res2
                       shi = 'Var2 -> Var1'
                    elif res3 != None:
                       res = res3
                       shi = 'Var1 -> Var2'


                    if res != None:
                       if res1 != None:
                         rs_nosh.append(res1[0])
                         pvals_nosh.append(res1[1])
                       else:
                         rs_nosh.append(None)
                         pvals_nosh.append(None)

                       if res2 != None:
                          rs_v2_pr_v1.append(res2[0])
                          pvals_v2_pr_v1.append(res2[1])
                       else:
                          rs_v2_pr_v1.append(None)
                          pvals_v2_pr_v1.append(None)

                       if res3 != None:
                          rs_v1_pr_v2.append(res3[0])
                          pvals_v1_pr_v2.append(res3[1])
                       else:
                          rs_v1_pr_v2.append(None)
                          pvals_v1_pr_v2.append(None)
                    else:
                        rs_nosh.append(None)
                        pvals_nosh.append(None)
                        rs_v2_pr_v1.append(None)
                        pvals_v2_pr_v1.append(None)
                        rs_v1_pr_v2.append(None)
                        pvals_v1_pr_v2.append(None)

                    if res != None:
                       shift.append(shi)
                       val1.append(cols[i])
                       val2.append(cols[j])
                       rs.append(res[0])
                       pvals.append(res[1])
                    else:
                       shift.append('x')
                       val1.append(cols[i])
                       val2.append(cols[j])
                       rs.append('R')
                       pvals.append(1.0)
                        
                    # now the accumulation analysis
                    best_p = 1.0
                    best_r = None
                    best_sigma = None
                    best_dir = None
                
                    for s in range(len(sigmas)): 

                        # first one direction
                        r_acc,p_acc = accumulation_stats[s]
                        if not numpy.isnan(p_acc[i,j]) and p_acc[i,j] < best_p:
                            best_p = p_acc[i,j]
                            best_r = r_acc[i,j]
                            best_sigma = sigmas[s]
                            best_dir = 'Var1 -> Var2'
    
                        # then the second direction
                        if not numpy.isnan(p_acc[j,i]) and p_acc[j,i] < best_p:
                            best_p = p_acc[j,i]
                            best_r = r_acc[j,i]
                            best_sigma = sigmas[s]
                            best_dir = 'Var2 -> Var1'

                    acc_p.append(best_p)
                    acc_r.append(best_r)
                    acc_dir.append(best_dir)
                    acc_sigma.append(best_sigma)

    set_table(None,None,None,source,relationships)


def set_table(attr, old, new, source,relationships):
    if val1 != []:
        # filter out my p
        select1 = numpy.array(pvals) <= ui['max_p'].value

        # filter out by variable selection 
        if ui['show_which'].active==1:
            select2 = numpy.logical_or(numpy.array(val1) == ui["select_variable"].value,numpy.array(val2) == ui["select_variable"].value)
        else:
            select2 = numpy.array(pvals)*0==0        

        # filter out by ignore and black list
        if ui["hide_list_choice"].active == 0:
            select3 = numpy.array(pvals)*0==0        
        elif ui["hide_list_choice"].active == 1:
            select3 = numpy.logical_not(numpy.logical_or(relationships.is_on_ignore_list(zip(val1,val2)),relationships.is_on_black_list(zip(val1,val2))))
        elif ui["hide_list_choice"].active == 2:
            select3 = numpy.logical_not(relationships.is_on_black_list(zip(val1,val2)))

        select = numpy.logical_and(select1,numpy.logical_and(select2,select3))

        source.data = {'Variable 1' : numpy.array(val1)[select], 
                       'Variable 2' : numpy.array(val2)[select], 
                       'R' : numpy.nan_to_num(rs)[select], 
                       'p-value' : numpy.nan_to_num(pvals)[select], 
                       'shift' : numpy.nan_to_num(shift)[select],
                       'r_no_shift' : numpy.nan_to_num(rs_nosh)[select], 
                       'p_no_shift' : numpy.nan_to_num(pvals_nosh)[select], 
                       'r_no_v1_to_v2' : numpy.nan_to_num(rs_v1_pr_v2)[select], 
                       'p_no_v1_to_v2' : numpy.nan_to_num(pvals_v1_pr_v2)[select], 
                       'r_no_v2_to_v1' : numpy.nan_to_num(rs_v2_pr_v1)[select], 
                       'p_no_v2_to_v1' : numpy.nan_to_num(pvals_v2_pr_v1)[select], 
                       'Accumulation analysis P' : numpy.nan_to_num(acc_p)[select], 
                       'Accumulation analysis R' : numpy.nan_to_num(acc_r)[select], 
                       'Accumulation analysis Sigma' : numpy.nan_to_num(acc_sigma)[select], 
                       'Accumulation analysis Dir' : numpy.nan_to_num(acc_dir)[select], 
                       }

def selection_execute_button(data,metadata,source,source_selection,relationships):
    selection_execute(None,None,None,data,metadata,source,source_selection,relationships)

def selection_execute(attr, old, new,data,metadata,source,source_selection,relationships):
    if len(set(ui["selection1"].value).intersection(set(ui["selection2"].value))) == 0:
        ui['message'].text = ''
        columns = [TableColumn(field=v,formatter=HTMLTemplateFormatter(template='<%= value %>')) for v in ui["selection2"].value]
        columns = [TableColumn(field='Variable name',title='')] + columns
        ui['sdt'].columns = columns

        
        m = [['N/A' for i in range(len(ui["selection1"].value))] for i in range(len(ui["selection2"].value))]

        for v1,v2,r12,r21,rns,p12,p21,pns in zip(val1,val2,rs_v1_pr_v2,rs_v2_pr_v1,rs_nosh,pvals_v1_pr_v2,pvals_v2_pr_v1,pvals_nosh):
            if ((v1 in ui["selection1"].value) and (v2 in ui["selection2"].value)) or ((v2 in ui["selection1"].value) and (v1 in ui["selection2"].value)):

               if ui['show_shift'].active == 1:
                  pv = pns
                  r = rns
               elif ui['show_shift'].active == 0:
                    if v1 in ui["selection1"].value and v2 in ui["selection2"].value:
                       pv = p12
                       r = r12
                    elif v2 in ui["selection1"].value and v1 in ui["selection2"].value:
                       pv = p21
                       r = r21                  
               elif ui['show_shift'].active == 2:
                    if v1 in ui["selection1"].value and v2 in ui["selection2"].value:
                       pv = p21
                       r = r21
                    elif v2 in ui["selection1"].value and v1 in ui["selection2"].value:
                       pv = p12
                       r = r12
                       
               if pv < 0.01:
                  cell = ('<span style="color:green">R=%.3g' % (r)) + (' (p=%.3g' % (pv)) + ')'     
               else:
                  cell = ('<span> R=%.3g' % (r)) + (' (p=%.3g' % (pv)) + ') '
                      
               if v1 in ui["selection1"].value and v2 in ui["selection2"].value:
                   m[ui["selection2"].value.index(v2)][ui["selection1"].value.index(v1)] = cell
               else:
                   m[ui["selection2"].value.index(v1)][ui["selection1"].value.index(v2)] = cell


        d = {c : m[i] for i,c in enumerate(ui["selection2"].value)}
        d['Variable name'] = list(ui["selection1"].value.copy())
        source_selection.data = d
    else:
        ui['message'].text ='Selections have to have no intersection.'
 
def update_selection(attr, old, new,categories):
    ui["select_variable"].options = list(categories[ui["select_category"].value])

def show_which(attr, old, new,categories,source,relationships):
    if new == 0:
       if len(ui['RightColumn'].children) == 2:
          ui['RightColumn'].children.pop()
       ui['dt'].visible = True
       if old == 1:
         ui['show_which_column'].children.pop(2)
         ui['show_which_column'].children.pop(1)
    elif new == 1:   
       if len(ui['RightColumn'].children) == 2:
          ui['RightColumn'].children.pop()
       ui['dt'].visible = True
       ui['show_which_column'].children.append(ui["select_category"]) 
       ui['show_which_column'].children.append(ui["select_variable"]) 
    else:   
       ui['RightColumn'].children.append(ui['SelectionColumn'])
       ui['dt'].visible = False
       if old == 1:
         ui['show_which_column'].children.pop(2)
         ui['show_which_column'].children.pop(1)


    set_table(None,None,None,source,relationships)

def switch_to_inspection(source,metadata,comparison_panel):
    if len(source.selected.indices) == 1:
        idx = source.selected.indices[0]

        comparison_panel.ui_elements['select_category1'].value = metadata['Category'].loc[source.data['Variable 1'][idx]]
        comparison_panel.ui_elements['select_variable1'].value = source.data['Variable 1'][idx]
        
        comparison_panel.ui_elements['select_category2'].value = metadata['Category'].loc[source.data['Variable 2'][idx]]
        comparison_panel.ui_elements['select_variable2'].value = source.data['Variable 2'][idx]
        
        scripts.create_app.tabs.active=0

def add_to_blacklist(source,relationships):
    print('Add to blacklist')
    for idx in source.selected.indices:
        relationships.add_on_black_list(source.data['Variable 1'][idx],source.data['Variable 2'][idx])
    source.selected.indices=[]
    set_table(None,None,None,source,relationships)        

def add_to_ignorelist(source,relationships):
    print('Add to ignore list')
    for idx in source.selected.indices:
        relationships.add_on_ignore_list(source.data['Variable 1'][idx],source.data['Variable 2'][idx])

    source.selected.indices=[]
    set_table(None,None,None,source,relationships)

def panel(data,categories,metadata,relationships,comparison_panel):

    source = ColumnDataSource(data={'Variable 1' : [], 'Variable 2' : [], 'R' : [], 'p-value' : [], 'shift' : [], 'r_no_sihdaft' : [], 'p_no_shift' : [], 'r_no_v1_to_v2' : [], 'p_no_v1_to_v2' : [], 'r_no_v2_to_v1' : [], 'p_no_v2_to_v1' : []})
    seletion_source = ColumnDataSource(data={'Var 1' : [], 'Var 2' : [], 'Var 3' : [], 'Var 4' : [],  'Var 5' : []})

    columns = [
        TableColumn(field="Variable 1"),
        TableColumn(field="Variable 2"),
        TableColumn(field="R",title='R best'),
        TableColumn(field="p-value",title='P best'),
        TableColumn(field="shift",title='best shift'),
        TableColumn(field="r_no_shift",title='R no-shift'),
        TableColumn(field="p_no_shift",title='P no-shift'),
        TableColumn(field="r_no_v1_to_v2",title='R V1->V2'),
        TableColumn(field="p_no_v1_to_v2",title='P V1->V2'),
        TableColumn(field="r_no_v2_to_v1",title='R V2->V1'),
        TableColumn(field="p_no_v2_to_v1",title='P V2->V1'),
        TableColumn(field="Accumulation analysis P",title='Accumulation analysis P'),
        TableColumn(field="Accumulation analysis R",title='Accumulation analysis R'),
        TableColumn(field="Accumulation analysis Sigma",title='Accumulation analysis Sigma'),
        TableColumn(field="Accumulation analysis Dir",title='Accumulation analysis Dir'),
    ]

    ui['dt'] = DataTable(source=source, columns=columns,sizing_mode="stretch_both",height=700)

    ui['sdt'] = DataTable(source=seletion_source, columns=[],sizing_mode="stretch_both",height=700)
  
    ui['button1'] = Button(label="Recalculate", button_type="success",width=200) 
    ui['button1'].on_click(partial(correlation_analysis,data=data,metadata=metadata,source=source,relationships=relationships))
    
    ui['button2'] = Button(label="Switch to inspection", button_type="success",width=200) 
    ui['button2'].on_click(partial(switch_to_inspection,source=source,metadata=metadata,comparison_panel=comparison_panel))

    ui['button3'] = Button(label="Add to ignore list", button_type="success",width=200) 
    ui['button3'].on_click(partial(add_to_ignorelist,source=source,relationships=relationships))

    ui['button4'] = Button(label="Add to black list", button_type="success",width=200) 
    ui['button4'].on_click(partial(add_to_blacklist,source=source,relationships=relationships))

    ui['max_p'] =  Slider(start=0.0, end=0.2, value=0.01, step=0.01, title="maximum p-value",width=200)
    ui['max_p'].on_change('value',partial(set_table,source=source,relationships=relationships))

    ui['show_which'] = RadioButtonGroup(labels=['show all','show selected','pick'], active=0)
    ui['show_which'].on_change('active',partial(show_which,categories=categories,source=source,relationships=relationships))

    ui["select_category"] = Select(title="Category",  options=list(categories.keys()), value = 'Fitbit')
    ui["select_variable"] = Select(title = 'Name', value = 'Steps', options = list(categories['Fitbit']))

    ui["select_category"].on_change('value', partial(update_selection,categories=categories))       
    ui["select_variable"].on_change('value', partial(set_table,source=source,relationships=relationships))

    ui['hide_list_choice'] = radio_button_group = RadioButtonGroup(labels=['All','Hide IL', 'Hide BL'], active=1)
    ui["hide_list_choice"].on_change('active', partial(set_table,source=source,relationships=relationships))

    ui['show_which_column'] = Column(ui['show_which'],width=200)

    ui['dt_pckr_start']=DatePicker(title='Select start',min_date=date(2021,3,1),max_date=date.today(),value=date(2021,3,1),width=100)
    ui['dt_pckr_end']=DatePicker(title='Select end',min_date=date(2021,3,1),max_date=date.today(),value=date.today(),width=100)

    ui['selection1'] = MultiChoice(value=[], options=list(data.columns))
    ui['selection2'] = MultiChoice(value=[], options=list(data.columns))

    ui['selection_execute'] = Button(label="Recalculate selection", button_type="success",width=200) 
    ui['selection_execute'].on_click(partial(selection_execute_button,data=data,metadata=metadata,source=source,source_selection=seletion_source,relationships=relationships))

    ui['show_shift'] = RadioButtonGroup(labels=['X->Y','No Shift','Y->X'], active=1)
    ui['show_shift'].on_change('active',partial(selection_execute,data=data,metadata=metadata,source=source,source_selection=seletion_source,relationships=relationships))

    ui['message']  = Paragraph(text="")

    ui['SelectionColumn'] = Column(Row(Paragraph(text="X: "),ui['selection1']),Row(Paragraph(text="Y: "),ui['selection2']),Row(ui['selection_execute'],ui['show_shift'],ui['message']),ui['sdt'],sizing_mode="stretch_both")

    ui['RightColumn'] = Column(ui['dt'],sizing_mode="stretch_both")

    layout = Row(Column(Row(ui['dt_pckr_start'],ui['dt_pckr_end']),ui['button1'],Div(text="""<hr width=240px>"""),ui['max_p'],ui['show_which_column'],Paragraph(text="View:"),ui['hide_list_choice'],ui['button2'],ui['button3'],ui['button4']),Spacer(width=50),ui['RightColumn'],sizing_mode="stretch_both")
    
    panel = TabPanel(child=layout, title="Correlations")
    
    return panel
