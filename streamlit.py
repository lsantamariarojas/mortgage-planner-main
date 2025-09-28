import numpy as np
import pandas as pd
import re

from frontend.plotsHelpers import plotters
from dataFetcher import dataFetcher

import streamlit as st
import streamlit.components.v1 as components
import json




with open('./frontend/defaults.json', 'rb') as file:
    DEFAULTS = json.load(file)

# ------------------------------------------------------------
#
#                  Visual settings and functions
#
# ------------------------------------------------------------

st.set_page_config(
    page_title="Mortgage Calculator", page_icon=":moneybag:", initial_sidebar_state="collapsed"
)

# @st.cache_resource
# def local_css(file_name):
#     with open(file_name) as f:
#         st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# local_css("./frontend/style.css")


sidebar = st.sidebar.markdown("**First select the data range you want to analyze:** 👇")
with sidebar:    
    with st.form(key = 'columns_in_form'):
        
        form_values = DEFAULTS.copy()
        for _key, _vals in DEFAULTS.items():
            if _vals['max'] <= 1:
                form_values[_key] = st.number_input(
                        _vals['name'], 
                        min_value = float(_vals['min']), 
                        max_value = float(_vals['max']), 
                        value = _vals['default'], 
                        step = 0.0001, 
                        format = '%f', 
                        help = _vals['help']
                        )
            else:
                form_values[_key] = st.number_input(
                        _vals['name'], 
                        min_value = _vals['min'], 
                        max_value = _vals['max'], 
                        value = _vals['default'], 
                        step = 100, 
                        format = '%d', 
                        help = _vals['help']
                        )
        
        submit = st.form_submit_button('Simulate')

if not submit:
    # if False:
    st.title('Welcome to the Mortgage Simulator')
    st.text('Please open the side bar and submit your values to simulate...')

else:

    increments = 500
    opt_result = []
    heat_plot = []
    plot_3d = []
    scenarios_plot = []
    cost_anal_plot = []
    saving_mortgages_comp_plot = []
    table_plot = []

    for i in range(3):
    
        calculator = dataFetcher( 
                rent_price_growth = form_values['RENT_GROWTH'],
                rent_price = form_values['RENT_PRICE'],
                house_price_growth = form_values['HOUSE_PRICE_GROWTH'],
                house_price = form_values['HOUSE_PRICE'],
                monthly_mortgage_interes = form_values['INTEREST'],
                intallment_threshold = form_values['INSTALLMENT_THRESH'] + increments * i,
                savings_per_month = form_values['SAVINGS_PER_MONTH'],
                etf_growth = form_values['SAVINGS_GROWTH'],
                initial_etf_savings = form_values['INITIAL_SAVINGS']
                )


        opt_result.append(calculator.get_optimal_result()[0])

        X, Y, Z = calculator.get_data_for_cost_plots()
        plots = plotters(X = X, Y = Y, Z = Z)

        heat_plot.append(plots.continuous_heatmap(show = False))
        plot_3d.append(plots.cost_3d(show = False))

        scenarios_results = calculator.get_scenarios()

        scenario_1 = scenarios_results['scenario1']
        scenarios_plot.append(plots.scenerio_comp_plot(
                        total_periods = scenario_1['sub_total_periods_arr'], 
                        suboptimal_cost_arr = scenario_1['suboptimal_cost_arr'], 
                        optimal_cost_arr = scenario_1['optimal_cumcost'], 
                        month_start_optimal = scenario_1['months_to_wait_opt'],
                        show = False
                        )
                    )
        

        scenario_4 = scenarios_results['scenario4']

        iter_cost_plt1, iter_cost_plt2 = plots.scenerio_grid_plot(
                        total_periods = scenario_4['total_periods'], 
                        interest_payments = scenario_4['interest_payments'], 
                        rent_prices = scenario_4['rent_prices'],
                        month_start_optimal = scenario_4['months_to_wait'], 
                        house_prices = scenario_4['house_prices'], 
                        saved_amounts = scenario_4['saved_amounts'], 
                        show = False
                        )

        cost_anal_plot.append([iter_cost_plt1, iter_cost_plt2])


        scenario_2 = scenarios_results['scenario2']
        starting_point = scenario_4['total_periods'][-1] + 1


        saving_mortgages_comp_plot.append(plots.future_savings_house_plot(
                            starting_point = starting_point, 
                            savings_scenario_arr = scenario_2['savings_scenario_arr'], 
                            house_scenario_arr = scenario_2['house_scenario_arr'], 
                            show = False
                            )
                    )

        results_data = scenarios_results['scenario3']['compiled_data'].sort_values(by = ['cost_function', 'months_to_wait', 'mortgage_years'], ascending = True)
        results_data.columns = [re.sub('_', '<br>', i) for i in results_data.columns]

        table_plot.append(plots.plot_table(results_data))


    def table_footer():
        return st.html('''<sub>*** months_to_wait: Months until entering into mortgage<br>&emsp;cost_function: Total costs that sums rent paid until before entering a mortgage, the interest on the mortgage and the 
                penalization of house appreciation against today's value as a cost of opportunity<br> 
                &emsp;payments: payment installments for the mortgage<br>&emsp;at_n: point in time when that scenarion enterred mortgage</sub>''')



    tab1, tab2 = st.tabs(["Submitted Scenario", "Sensitivity Analysis"])

        
    with tab1:

            # Print the results
        tab1.text(f"Optimal solution: Months to save until buying: {int(np.ceil(opt_result[0].x[0]))}, Mortgage Years: {int(np.ceil(opt_result[0].x[1]))}")
        tab1.text(f"""Optimal Total cost: Rents to save the needed money + Mortgage Interest 
                         + House Appreciation Oportunity cost: {opt_result[0].fun}""")  

        st.plotly_chart(table_plot[0], use_container_width=True, key = 'la_tablacsa') 

        table_footer()
        

        r1_t1, r1_t2 = tab1.columns((1,1))       

        r1_t2.plotly_chart(heat_plot[0], use_container_width=True)       
        r1_t1.plotly_chart(plot_3d[0], use_container_width=True)   

        r2_t1, r2_t2 = tab1.columns((1,1))    

        r2_t2.plotly_chart(scenarios_plot[0], use_container_width=True)       
        r2_t2.plotly_chart(saving_mortgages_comp_plot[0], use_container_width=True)       
        r2_t1.plotly_chart(cost_anal_plot[0][0], use_container_width=True)
        r2_t1.plotly_chart(cost_anal_plot[0][1], use_container_width=True)



    with tab2:

        for i in range(1, 3):
        
            tab2.html(f'''<h2>With Installment at {form_values['INSTALLMENT_THRESH'] + 500 * i}</h2>''')

            tab2.text(f"Optimal solution: Months to save until buying: {int(opt_result[i].x[0])}, Mortgage Years: {int(opt_result[i].x[1])}")
            tab2.text(f"""Optimal Total cost: Rents to save the needed money + Mortgage Interest 
                         + House Appreciation Oportunity cost: {opt_result[i].fun}""")  

            st.plotly_chart(table_plot[i], use_container_width=True) 

            table_footer()

            r2_t1, r2_t2 = tab2.columns((1,1))    

            r2_t2.plotly_chart(scenarios_plot[i], use_container_width=True)       
            r2_t2.plotly_chart(heat_plot[i], use_container_width=True)       
            r2_t1.plotly_chart(cost_anal_plot[i][0], use_container_width=True)
            r2_t1.plotly_chart(cost_anal_plot[i][1], use_container_width=True)



    st.html('''<sub>Disclaimer: The calculator doesn't take into account taxes of any type (capital gains or property), insurance costs or any other cost no refer to in the dashboard</sub>''')
