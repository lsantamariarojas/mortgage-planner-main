from backend.financialSim import financialEstimator   
import pandas as pd
import numpy as np


class dataFetcher(financialEstimator):

    def __init__(
        self, 
        rent_price_growth,
        rent_price,
        house_price_growth,
        house_price,
        monthly_mortgage_interes,
        intallment_threshold,
        savings_per_month,
        etf_growth,
        initial_etf_savings
        ):

        super().__init__(
                    rent_price_growth = rent_price_growth,
                    rent_price = rent_price,
                    house_price_growth = house_price_growth,
                    house_price = house_price,
                    monthly_mortgage_interes = monthly_mortgage_interes,
                    intallment_threshold = intallment_threshold,
                    savings_per_month = savings_per_month,
                    etf_growth = etf_growth,
                    initial_etf_savings = initial_etf_savings
                        )

        self.__opt_result = None
        self.__opt_verbose = None
        self.__all_sub_optimal = None

    @property
    def opt_result(self):
        return self.__opt_result
        
    @property
    def opt_verbose(self):
        self.__opt_verbose

    @property
    def all_sub_optimal(self):
        self.__all_sub_optimal


    def get_optimal_result(self):
        self.__opt_result, self.__opt_verbose = self.run_simulation()
        return self.opt_result, self.opt_verbose


    def get_result_dataframe(self):
        if type(self.__opt_result) == type(None):
            self.get_optimal_result()

        sub_opt_steps = pd.DataFrame(self.__opt_verbose.decreasing_list_calls_inp, columns = ['months_to_wait', 'mortgage_years'])
        sub_opt_steps['cost_function'] = self.__opt_verbose.decreasing_list_calls_res

        _ = self.cost_grid()

        sub_optimal_grid = pd.DataFrame(self.reducing_steps, columns = ['steps', 'months_to_wait', 'mortgage_years', 'cost_function'])
        sub_optimal_grid.head(10)
        # sub_optimal_grid.iloc[-1 ,:]
        to_append = sub_optimal_grid.tail(20).head(5)

        all_sub_optimal = pd.concat([
                        sub_opt_steps[sub_opt_steps['cost_function'] != np.inf].tail(5).head(4),
                        sub_optimal_grid.sample(5)
                        ], axis = 0)


        all_sub_optimal.reset_index(drop = True, inplace = True)

        self.__all_sub_optimal = all_sub_optimal

        return all_sub_optimal


    def get_data_for_cost_plots(self):
        if type(self.__all_sub_optimal) == type(None):
            self.get_result_dataframe()
        return self.months_wait, self.mortgage_years, self.Z

    def get_scenarios(self):
        if type(self.__all_sub_optimal) == type(None):
            self.get_result_dataframe()
        scenarios_results = self.calculate_scenarios(opt_results_obj = self.__opt_result, sub_optimal_df = self.__all_sub_optimal)
        return scenarios_results


