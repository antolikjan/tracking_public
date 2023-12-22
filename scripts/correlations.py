from functools import partial
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Row, Column, Button, TableColumn, DataTable, Spacer, Slider, RadioButtonGroup, Select, DatePicker, Paragraph, Div, MultiChoice, HTMLTemplateFormatter, Paragraph, Panel
from scripts.data import both_valid, data_aquisition_overlap_non_nans
import scipy.stats
import numpy
import scripts.create_app
import scripts.comparison
from datetime import datetime
from datetime import date
from scripts.data import filter_data

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
    sigmas = [2,4]
    convolved = []
    for s in sigmas:
        print(s)
        convolved.append(filter_data('PastGauss',data.loc[selected_range,:].to_numpy(),s)[1])

    for i in range(len(cols)):
        print(i)
        for j in range(i+1,len(cols)): 

            # make sure both variables are numeric
            if metadata['Units'].loc[cols[i]] != 'string' and metadata['Units'].loc[cols[j]] != 'string':

                    x = data[cols[i]][selected_range].to_numpy()
                    y = data[cols[j]][selected_range].to_numpy()

                    # let's calculate the correlations only for positions where both values are defined and 
                    d1,d2 = data_aquisition_overlap_non_nans(x,y)
                    d1_shift1,d2_shift1 = data_aquisition_overlap_non_nans(x[1:],y[:-1])
                    d1_shift2,d2_shift2 = data_aquisition_overlap_non_nans(x[:-1],y[1:])

                    # we will not calculate correlations if variance of one of the variables within overlapping positions is zero
                    # and we will not compute correlations if there are less then 21 points of overlap between the two data vectors
                    if len(d1) > 20 and numpy.var(d1) != 0 and numpy.var(d2) != 0:
                            res1 = scipy.stats.linregress(d1,d2)
                    else:
                            res1 = None

                    if len(d1_shift1) > 20 and numpy.var(d1_shift1) != 0 and numpy.var(d2_shift1) != 0:
                            res2 = scipy.stats.linregress(d1_shift1,d2_shift1)
                    else:
                            res2 = None

                    if len(d1_shift2) > 20 and numpy.var(d1_shift2) != 0 and numpy.var(d2_shift2) != 0:
                            res3 = scipy.stats.linregress(d1_shift2,d2_shift2)
                    else:
                            res3 = None

                    res = None                       
                    if res1 != None and (res2 == None or res1.pvalue < res2.pvalue) and (res3 == None or res1.pvalue < res3.pvalue):
                       res = res1
                       shi = '=='
                    elif res2 != None and (res3 == None or res2.pvalue < res3.pvalue):  
                       res = res2
                       shi = 'Var2 -> Var1'
                    elif res3 != None:
                       res = res3
                       shi = 'Var1 -> Var2'


                    if res != None:
                       if res1 != None:
                         rs_nosh.append(res1.rvalue)
                         pvals_nosh.append(res1.pvalue)
                       else:
                         rs_nosh.append(None)
                         pvals_nosh.append(None)

                       if res2 != None:
                          rs_v2_pr_v1.append(res2.rvalue)
                          pvals_v2_pr_v1.append(res2.pvalue)
                       else:
                          rs_v2_pr_v1.append(None)
                          pvals_v2_pr_v1.append(None)

                       if res3 != None:
                          rs_v1_pr_v2.append(res3.rvalue)
                          pvals_v1_pr_v2.append(res3.pvalue)
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
                       rs.append(res.rvalue)
                       pvals.append(res.pvalue)
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
                        d1,d2 = data_aquisition_overlap_non_nans(convolved[s][:,i],y)
                        if numpy.var(d1) > 0.00000000000000001 and numpy.var(d2) > 0.00000000000000001 and len(d1)>= 5:

                            res = scipy.stats.linregress(d1,d2)
        
                            if res.pvalue < best_p:
                                    best_p = res.pvalue
                                    best_r = res.rvalue
                                    best_sigma = sigmas[s]
                                    best_dir = 'Var1 -> Var2'
    
                        # then the second direction
                        d1,d2 = data_aquisition_overlap_non_nans(convolved[s][:,j],x)
                        if numpy.var(d1) > 0.00000000000000001 and numpy.var(d2) > 0.00000000000000001 and len(d1)>= 5:
                            res = scipy.stats.linregress(d1,d2)
        
                            if res.pvalue < best_p:
                                best_p = res.pvalue
                                best_r = res.rvalue
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

        print(len(pvals))                    
        print(len(pvals_nosh))
        print(len(acc_p))     
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
    print(old)
    print(new)
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
    
    panel = Panel(child=layout, title="Correlations")
    
    return panel
