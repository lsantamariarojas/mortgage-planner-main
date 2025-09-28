import numpy as np
import pandas as pd

class financialFunctions:
    
    @staticmethod
    def future_value(period, interest, present_value = 0, payment = 0):
        present_val = present_value * (1 + interest)**period
        payment_val = payment / interest * ((1 + interest)**period - 1)
        return present_val + payment_val


    @staticmethod
    def payments(principal, interest, periods = 30 * 12):
        return principal * (interest * (1 + interest)**periods) / ((1 + interest)**periods - 1) 

    @staticmethod
    def total_interest(principal, interest, periods):
        return financialFunctions.payments(principal, interest, periods) * periods - principal 

    @staticmethod
    def principal_payments(current_period, initial_principal, interest, total_periods):
        payment = financialFunctions.payments(principal = initial_principal, interest = interest, periods = total_periods)
        principal = initial_principal
        for i in range(int(current_period)):
            principal -= payment - principal * interest
        return payment - principal * interest
        

    # @staticmethod
    # def remaining_principal_n_period(initial_principal, interest, current_period, total_periods):
    #     period_range = np.arange(1, current_period + 1, 1, dtype=int)
        
    #     accum_principal_pay = np.apply_along_axis(
    #                                     principal_payments,
    #                                     0, 
    #                                     period_range, 
    #                                     interest = interest, 
    #                                     present_value = initial_principal,
    #                                     total_periods = total_periods
    #                                     )
    #     return float(initial_principal - np.sum(accum_principal_pay))



from scipy.optimize import differential_evolution
from backend.callBacksWrapper import Simulator
import numpy as np


class financialEstimator(Simulator, financialFunctions):
    def __init__(self,
                rent_price_growth,
                rent_price,
                house_price_growth,
                house_price,
                monthly_mortgage_interes,
                intallment_threshold,
                savings_per_month,
                etf_growth,
                initial_etf_savings = 0
                ):

        self.rent_price_growth = rent_price_growth
        self.rent_price = rent_price
        self.house_price_growth = house_price_growth
        self.house_price = house_price
        self.monthly_mortgage_interes = monthly_mortgage_interes
        self.installment_threshold = intallment_threshold
        self.savings_per_month = savings_per_month
        self.etf_growth = etf_growth
        self.initial_etf_savings = initial_etf_savings
        self.__bounds =  [(1, 40 * 12), (1, 30)]

    @property
    def bounds(self):
        return self.__bounds

        
    def objective_function(self, x):

        x_0 = np.round(x[0]).astype(int) # Months to wait
        x_1 = np.round(x[1]).astype(int) # Mortgage years

        future_house_val = financialFunctions.future_value(
                                                    period = x_0, 
                                                    interest = self.house_price_growth, 
                                                    present_value = self.house_price, 
                                                    payment = 0
                                                    )
        future_saved_money = financialFunctions.future_value(
                                                    period = x_0, 
                                                    interest = self.etf_growth, 
                                                    present_value = self.initial_etf_savings, 
                                                    payment = self.savings_per_month
                                                    )
        mortgage_interest = financialFunctions.total_interest(
                                                    principal = future_house_val - future_saved_money, 
                                                    interest = self.monthly_mortgage_interes, 
                                                    periods = x_1 * 12
                                                    )
        total_rent_paid = financialFunctions.future_value(
                                                    period = x_0, 
                                                    interest = self.rent_price_growth, 
                                                    present_value = 0, 
                                                    payment = self.rent_price
                                                    )
        
        house_appreciation_cost = future_house_val - self.house_price
        

        monthly_payments = financialFunctions.payments(
                                                principal = future_house_val - future_saved_money, 
                                                interest = self.monthly_mortgage_interes, 
                                                periods = x_1 * 12
                                                )

        if monthly_payments > self.installment_threshold:
            # print('Monthly payment too high: ', monthly_payments)
            return np.inf
        
        if future_saved_money > future_house_val:
            return np.inf

        # print('At step: ',x_0, x_1 ,'house val: ', future_house_val, ', saved mon: ', future_saved_money, ', tot int: ', mortgage_interest, ', tot_rent: ', total_rent_paid, ', paym: ', monthly_payments)
        
        return mortgage_interest + total_rent_paid + house_appreciation_cost


    def cost_grid(self):

        # Generate data for the heatmap (example: 2D Gaussian function)
        months_wait = np.arange(self.bounds[0][0], self.bounds[0][1], dtype= int)
        mortgage_years = np.arange(self.bounds[1][0], self.bounds[1][1], dtype= int)

        Z = np.zeros(shape = (len(mortgage_years), len(months_wait)))    
        
        reducing_steps = []
        mini = np.inf
        # INSTALLMENT_THRESH = 5000
        step = 1

        for i, months in enumerate(months_wait):
            for j, mortgage in enumerate(mortgage_years):
                Z[j, i] = self.objective_function([months , mortgage])
                if Z[j, i] < mini:
                    # print(months, mortgage, Z[j, i])
                    mini = Z[j, i]
                    reducing_steps.append((step, months, mortgage, Z[j, i]))
                    step += 1

        self.months_wait = months_wait
        self.mortgage_years = mortgage_years
        self.Z = Z
        self.reducing_steps = reducing_steps

        return (months_wait, mortgage_years, Z, reducing_steps)


    def run_simulation(self):
        
        wrapper = Simulator(self.objective_function)

        result = differential_evolution(
                    func = wrapper.simulate, 
                    bounds = self.bounds, 
                    callback = wrapper.callback
                    )

        return result, wrapper
    

    def calculate_scenarios(self, opt_results_obj, sub_optimal_df):
        months = int(np.round(opt_results_obj.x[0]))
        mortgage_years = int(np.round(opt_results_obj.x[1]))

        total_periods = np.arange(0, months + (mortgage_years + 30) * 12, dtype = int)
        mortgage_periods = np.arange(0, mortgage_years * 12, dtype = int)
        rent_prices = np.apply_along_axis(financialEstimator.future_value, 0, total_periods, payment = self.rent_price, interest = self.rent_price_growth)

        house_prices = np.apply_along_axis(financialEstimator.future_value, 0, total_periods, present_value = self.house_price, interest = self.house_price_growth)
        saved_amounts = np.apply_along_axis(financialEstimator.future_value, 0, total_periods, present_value = self.initial_etf_savings, interest = self.etf_growth, payment = self.savings_per_month)

        # print(saved_amounts)


        house_appreciation_cost = house_prices - self.house_price
        # INITIAL_ETF_SAVINGS



        principal_payments = [
                                financialEstimator.principal_payments(
                                            current_period = int(i), 
                                            initial_principal = house_prices[months] - saved_amounts[months], 
                                            interest = self.monthly_mortgage_interes, 
                                            total_periods = mortgage_years * 12
                                        )
                                for i in mortgage_periods
                            ]
        # print("principal_payments: ", principal_payments)

        payments = financialEstimator.payments(principal = house_prices[months] - saved_amounts[months], interest = self.monthly_mortgage_interes, periods = mortgage_years * 12)
        # print("payments: ", payments)

        interest_payments = payments - principal_payments

        optimal_cumcost = np.append(rent_prices[:months] + house_appreciation_cost[:months], np.cumsum(np.append(interest_payments[0] + rent_prices[:months][-1] + house_appreciation_cost[months], interest_payments[1:])))

        '''
        **************************************
        This part is for the suboptimal plots
        **************************************
        '''


        max_period = sub_optimal_df['months_to_wait'].max()
        max_cost = sub_optimal_df['cost_function'].max()

        sub_total_periods = np.arange(0, max_period + 30 * 12 + 1, dtype = int)
        house_prices_suboptimal = np.apply_along_axis(financialEstimator.future_value, 0, sub_total_periods, present_value = self.house_price, interest = self.house_price_growth)
        saved_amounts_suboptimal = np.apply_along_axis(financialEstimator.future_value, 0, sub_total_periods, present_value = self.initial_etf_savings, interest = self.etf_growth, payment = self.savings_per_month)
        rent_prices_suboptimal = np.apply_along_axis(financialEstimator.future_value, 0, sub_total_periods, payment = self.rent_price, interest = self.rent_price_growth)
        house_appreciation_suboptimal = house_prices_suboptimal - self.house_price


        suboptimal_int = {}
        suboptimal_pay = {}
        suboptimal_cost = []
        for _, row in sub_optimal_df.iterrows():
            iter_months = int(np.round(row['months_to_wait'])) + 1
            iter_mortgage = int(np.round(row['mortgage_years']))

            if self.objective_function([iter_months, iter_mortgage]) != np.inf:
                # print([iter_months, iter_mortgage], self.objective_function([iter_months, iter_mortgage]))

                iter_mortgage_periods = np.arange(0, iter_mortgage * 12 + 1, dtype = int)

                iter_principal = [financialEstimator.principal_payments(
                                            current_period = int(i), 
                                            initial_principal = house_prices_suboptimal[iter_months] - saved_amounts_suboptimal[iter_months], 
                                            interest = self.monthly_mortgage_interes, 
                                            total_periods = iter_mortgage * 12
                                        )
                                for i in iter_mortgage_periods
                            ]
                iter_payments = financialEstimator.payments(principal = house_prices_suboptimal[iter_months] - saved_amounts_suboptimal[iter_months], interest = self.monthly_mortgage_interes, periods = iter_mortgage * 12)

                suboptimal_int.update({'{0}-{1}'.format(iter_months, iter_mortgage): iter_payments - iter_principal})
                suboptimal_pay.update({'{0}-{1}'.format(iter_months, iter_mortgage): iter_payments})
                # print(iter_principal, iter_payments)

                # print('outer house val: ', house_prices_suboptimal[iter_months], ', saved mon: ', saved_amounts_suboptimal[iter_months]
                #       , ', tot int: ', sum(iter_payments - iter_principal), ', tot_rent: ', rent_prices_suboptimal[:iter_months + 1][-1],
                #        ', paym: ', iter_payments,'\n\n')
                suboptimal_cost.append((iter_months, np.append(
                                                    rent_prices_suboptimal[:iter_months + 1] + house_appreciation_suboptimal[:iter_months + 1],
                                                    np.cumsum(np.append(
                                                        (iter_payments - iter_principal)[0] + rent_prices_suboptimal[:iter_months + 1][-1] + house_appreciation_suboptimal[:iter_months + 1][-1],
                                                        (iter_payments - iter_principal)[1:]
                                                        )
                                                    )
                                                )
                                            )
                                        )


        '''
        ********************************************
        This part is for savings vs house scenarios
        ********************************************
        '''

        complete_steps = months + mortgage_years * 12

        savings_scenario = saved_amounts[complete_steps:] - rent_prices[complete_steps:]

        optimal_realized_cumcost = np.append(rent_prices[:months], np.cumsum(np.append(interest_payments[0] + rent_prices[:months][-1], interest_payments[1:])))

        final_house_val = house_prices[complete_steps] - optimal_realized_cumcost[-1]
        house_scenario = np.append(final_house_val, saved_amounts[:30 * 12] + final_house_val)


        '''
        ********************************************
        This part is for summary table
        ********************************************
        '''


        def sub_opt_int_fun(x, dictio):
            try:
                return dictio['{0}-{1}'.format(int(np.round(x['months_to_wait'] + 1)), int(np.round(x['mortgage_years'])))]
            except:
                return [0]


        sub_optimal_df['interest'] = sub_optimal_df.apply(lambda x: sum(sub_opt_int_fun(x, dictio = suboptimal_int)), axis = 1)
        sub_optimal_df['payments'] = sub_optimal_df.apply(lambda x: sub_opt_int_fun(x, dictio = suboptimal_pay), axis = 1)
        cols_to_keep = [i for i in sub_optimal_df.columns if i != 'steps']


        optimal_pd = pd.DataFrame([[months, mortgage_years, opt_results_obj.fun, sum(interest_payments), payments]], columns = cols_to_keep)

        all_pd = pd.concat([sub_optimal_df[cols_to_keep], optimal_pd], axis = 0)

        all_pd['months_to_wait'] = all_pd['months_to_wait'].astype(int)
        all_pd['mortgage_years'] = all_pd['mortgage_years'].astype(int)

        all_pd['house_val_at_n'] = all_pd.apply(lambda x: house_prices_suboptimal[int(x['months_to_wait'] + 1)], axis = 1)
        all_pd['savings_at_n'] = all_pd.apply(lambda x: saved_amounts_suboptimal[int(x['months_to_wait'] + 1)], axis = 1)
        all_pd['rent_paid_at_n'] = all_pd.apply(lambda x: rent_prices_suboptimal[int(x['months_to_wait'] + 1)], axis = 1)
        all_pd['house_appreciation_cost'] = all_pd.apply(lambda x: house_appreciation_suboptimal[int(x['months_to_wait'] + 1)], axis = 1)



        all_pd = all_pd.loc[all_pd['interest'] != 0, ['months_to_wait', 'mortgage_years', 'cost_function', 'house_val_at_n', 'house_appreciation_cost', 'savings_at_n',
            'rent_paid_at_n', 'interest', 'payments']]
        
        for i in ['house_appreciation_cost', 'cost_function', 'house_val_at_n', 'savings_at_n',
            'rent_paid_at_n', 'interest', 'payments']:
            all_pd[i] = all_pd[i].apply(lambda x: round(x, 2))
        
        all_pd.columns = ['months_to_wait', 'mortgage_years', 'cost_function', 'house_value_at_step n', 'house_appreciation_cost', 'savings_at_step n',
            'rent_paid_at_step n', 'interest', 'payments']
        
        all_pd.sort_values(by = 'cost_function', inplace = True)
        all_pd.reset_index(drop = True, inplace = True)
     
        

        returning_dict = {
            'scenario1': {
                'sub_total_periods_arr': sub_total_periods,
                'suboptimal_cost_arr': suboptimal_cost,
                'optimal_cumcost': optimal_cumcost,
                'months_to_wait_opt': months
            },
            'scenario2': {
                'savings_scenario_arr': savings_scenario,
                'house_scenario_arr': house_scenario
            },
            'scenario3': {
                'compiled_data': all_pd
            },
            'scenario4': {
                'total_periods': total_periods,
                'house_prices': house_prices,
                'rent_prices': rent_prices,
                'saved_amounts': saved_amounts,
                'total_periods': np.arange(0, months + mortgage_years * 12, dtype = int),
                'interest_payments': interest_payments,
                'months_to_wait': months

            }
            
        }

        return returning_dict
