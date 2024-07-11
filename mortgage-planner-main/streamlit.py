import numpy as np
import pandas as pd
from frontend.plotsHelpers import plotters
import streamlit as st
import streamlit.components.v1 as components
import json

from backend.financialSim import financialEstimator    

with open('./frontend/defaults.json', 'rb') as file:
    DEFAULTS = json.load(file)

# ------------------------------------------------------------
#
#                  Visual settings and functions
#
# ------------------------------------------------------------

st.set_page_config(
    page_title="Mortgage Calculatoo", page_icon="🗡️", initial_sidebar_state="collapsed"
)

# @st.cache_resource
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css("./frontend/style.css")


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
    st.title('Welcome to the Mortgage Simulator')
    st.text('Please open the side bar and submit your values to simulate...')

else:

    calculator = financialEstimator( 
                        rent_price_growth = form_values['RENT_GROWTH'],
                        rent_price = form_values['RENT_PRICE'],
                        house_price_growth = form_values['HOUSE_PRICE_GROWTH'],
                        house_price = form_values['HOUSE_PRICE'],
                        monthly_mortgage_interes = form_values['INTEREST'],
                        intallment_threshold = form_values['INSTALLMENT_THRESH'],
                        savings_per_month = form_values['SAVINGS_PER_MONTH'],
                        etf_growth = form_values['SAVINGS_GROWTH'],
                        initial_etf_savings = form_values['INITIAL_SAVINGS']
                        )
   
    opt_result, opt_verbose = calculator.run_simulation()

    sub_opt_steps = pd.DataFrame(opt_verbose.decreasing_list_calls_inp, columns = ['months_to_wait', 'mortgage_years'])
    sub_opt_steps['cost_function'] = opt_verbose.decreasing_list_calls_res

    _ = calculator.cost_grid()

    sub_optimal_grid = pd.DataFrame(calculator.reducing_steps, columns = ['steps', 'months_to_wait', 'mortgage_years', 'cost_function'])
    sub_optimal_grid.head(10)
    # sub_optimal_grid.iloc[-1 ,:]
    to_append = sub_optimal_grid.tail(20).head(5)

    all_sub_optimal = pd.concat([
                    sub_opt_steps[sub_opt_steps['cost_function'] != np.inf].tail(5).head(4),
                    sub_optimal_grid.sample(5)
                    ], axis = 0)


    all_sub_optimal.reset_index(drop = True, inplace = True)

    plots = plotters(X = calculator.months_wait, Y = calculator.mortgage_years, Z = calculator.Z)

    heat_plot = plots.continuous_heatmap(show = False)
    plot_3d = plots.cost_3d(show = False)

    scenarios_results = calculator.calculate_scenarios(opt_results_obj = opt_result, sub_optimal_df = all_sub_optimal)

    scenario_1 = scenarios_results['scenario1']
    scenarios_plot = plots.scenerio_comp_plot(
                    total_periods = scenario_1['sub_total_periods_arr'], 
                    suboptimal_cost_arr = scenario_1['suboptimal_cost_arr'], 
                    optimal_cost_arr = scenario_1['optimal_cumcost'], 
                    month_start_optimal = scenario_1['months_to_wait_opt'],
                    show = False
                    
                    )
    

    scenario_4 = scenarios_results['scenario4']

    cost_anal_plot = plots.scenerio_grid_plot(
                    total_periods = scenario_4['total_periods'], 
                    interest_payments = scenario_4['interest_payments'], 
                    rent_prices = scenario_4['rent_prices'],
                    month_start_optimal = scenario_4['months_to_wait'], 
                    house_prices = scenario_4['house_prices'], 
                    saved_amounts = scenario_4['saved_amounts'], 
                    show = False
                    )


    scenario_2 = scenarios_results['scenario2']
    starting_point = scenario_4['total_periods'][-1] + 1


    saving_mortgages_comp_plot = plots.future_savings_house_plot(
                        starting_point = starting_point, 
                        savings_scenario_arr = scenario_2['savings_scenario_arr'], 
                        house_scenario_arr = scenario_2['house_scenario_arr'], 
                        show = False
                        )

    results_data = scenarios_results['scenario3']['compiled_data']




    tab1, tab2 = st.tabs(["intro", "start game"])

    

    
    with tab1:

            # Print the results
        tab1.text(f"Optimal solution: Months to save until buying: {int(opt_result.x[0])}, Mortgage Years: {int(opt_result.x[1])}")
        tab1.text(f"Optimal Total cost: Rents to save the needed money + Mortgage Interest: {opt_result.fun}")   

        r1_t1, r1_t2 = tab1.columns((1,1))       

        r1_t2.plotly_chart(heat_plot, use_container_width=True)       
        r1_t1.plotly_chart(plot_3d, use_container_width=True)   

        r2_t1, r2_t2 = tab1.columns((1,1))    

        r2_t2.plotly_chart(scenarios_plot, use_container_width=True)       
        r2_t2.plotly_chart(saving_mortgages_comp_plot, use_container_width=True)       
        r2_t1.plotly_chart(cost_anal_plot, use_container_width=True)
        


        




