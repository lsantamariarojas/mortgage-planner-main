import plotly.graph_objects as go
import numpy as np
from plotly.subplots import make_subplots


class plotters:

    def __init__(self, X, Y, Z):
        self.Z = Z
        self.X = X
        self.Y = Y
    
    
    def continuous_heatmap(self, show = False):

        # Example with annotations
        fig = go.Figure(data=go.Heatmap(
                        z = self.Z,
                        x = self.X,
                        y = self.Y,
                        colorscale = 'Viridis',
                        colorbar = dict(title = 'Total Cost'),
                        text=np.around(self.Z, decimals = 2))
                        )  # Rounded values as annotations

        fig.update_layout(
            title='Total Cost Mortgage Over Simulation Grid',
            yaxis=dict(title='Mortgage years'),
            xaxis=dict(title='Months to wait until buy'),
            height=400,  # Adjust height of the figure
            width=400    # Adjust width of the figure
        )

        if show:
            fig.show()

        return fig


    def cost_3d(self, show = False):
    
        X, Y = np.meshgrid(self.X, self.Y)

        # Create surface plot figure
        fig2 = go.Figure(data=[go.Surface(
                            z = self.Z,
                            x = X,
                            y = Y,
                            colorscale = 'Viridis'  
                            )])

        # Update layout properties
        fig2.update_layout(
            title='Total Cost Mortgage Over Simulation Grid',
            scene=dict(
                xaxis_title='Months to wait until buy',
                yaxis_title='Mortgage years',
                zaxis_title='Total Cost',
            ),
            width = 400,
            height = 400
        )

        if show:
            # Show plot
            fig2.show()

        return fig2


        
    
    @staticmethod
    def scenerio_comp_plot(total_periods, suboptimal_cost_arr, optimal_cost_arr, month_start_optimal, show = True):

        max_cost = max([i[1][-1] for i in suboptimal_cost_arr])

        fig = go.Figure()

        for i, tup in enumerate(suboptimal_cost_arr):

            color = f'rgba({39 + i * 10}, 148, 245, 0.5)'
            # Add trace for the first segment (before color change point)
            fig.add_trace(go.Scatter(x=total_periods[:len(tup[1])], y = tup[1], name=f'suboptimal {i}', line=dict(color=color, dash="dash")))

            fig.add_shape(
                type="line",
                x0=tup[0],
                y0=0,
                x1=tup[0],
                y1=max_cost * 1.05,  # Set y1 to the maximum y-axis value (for example, 1)
                line=dict(
                    color=color,
                    width=1
                )
            )


        fig.add_trace(go.Scatter(x=total_periods[:len(optimal_cost_arr)], y = optimal_cost_arr, name='Optimal', line=dict(color=f'rgba(39, 148, 245, 1)')))

        fig.add_shape(
                type="line",
                x0=month_start_optimal,
                y0=0,
                x1=month_start_optimal,
                y1=max_cost * 1.05,  # Set y1 to the maximum y-axis value (for example, 1)
                line=dict(
                    color=color,
                    width=1
                )
            )

        fig.update_layout(
            title='Three Vertically Stacked Line Charts in Different Frames',
            height=300,  # Adjust height of the figure
            width=800,   # Adjust width of the figure 

            title_x=0.5,    # Set title position to the middle horizontally
            title_y=0.95,   # Set title position closer to the top vertically
            xaxis_title_standoff=25,  # Adjust standoff for X axis titles
            yaxis_title_standoff=25,  # Adjust standoff for Y axis titles
            hoversubplots = 'axis',
            hovermode = 'x unified',
            # hoverdistance = -1,
        )

        if show:
            fig.show()

        return fig
    


    @staticmethod
    def scenerio_grid_plot(total_periods, interest_payments, rent_prices, month_start_optimal, house_prices, saved_amounts, show = True):

        max_step = total_periods[-1]
        padding_nan = np.repeat(np.nan, len(total_periods) - len(interest_payments))
        # Create figure with three vertically stacked frames
        fig = make_subplots(
            rows = 2, 
            cols = 1, 
            specs = [[{}], [{}]],
            vertical_spacing = 0.025,
            shared_xaxes = True
        )

        # Add trace for Line Chart 1: Sin(x) in Frame 1
        fig.add_trace(go.Scatter(x=total_periods, y=rent_prices, name='Rent prices',
                                yaxis='y1', showlegend = True, stackgroup = 'one'), 1, 1)

        fig.add_trace(go.Scatter(x=total_periods, y=np.append(padding_nan, interest_payments), name='Interest payment',
                                yaxis='y1', showlegend = True, stackgroup = 'two'), 1, 1)

        fig.add_shape(
            type="line",
            x0=month_start_optimal,
            y0=0,
            x1=month_start_optimal,
            y1=rent_prices[max_step] * 1.05,  # Set y1 to the maximum y-axis value (for example, 1)
            line=dict(
                color="black",
                width=3,
                dash="dashdot"
            ),
            row = 1,
            col = 1
        )




        fig.add_trace(go.Scatter(x=total_periods, y=house_prices,  name='House Prices',
                                yaxis='y2', stackgroup = 'one'), 2, 1)

        # Add trace for Line Chart 3: Tan(x) in Frame 3
        fig.add_trace(go.Scatter(x=total_periods, y=saved_amounts, name='Savings',
                                yaxis='y3', stackgroup = 'two'), 2, 1)



        fig.add_shape(
            type="line",
            x0=month_start_optimal,
            y0=0,
            x1=month_start_optimal,
            y1=max(np.append(house_prices[max_step], saved_amounts[max_step])) * 1.05,  # Set y1 to the maximum y-axis value (for example, 1)
            line=dict(
                color="black",
                width=3,
                dash="dashdot",
            ),
            row = 2,
            col = 1
        )

        # Update layout properties for Frame 1
        fig.update_layout(
            title='Three Vertically Stacked Line Charts in Different Frames',
            height=900,  # Adjust height of the figure
            width=800,   # Adjust width of the figure 

            title_x=0.5,    # Set title position to the middle horizontally
            title_y=0.95,   # Set title position closer to the top vertically
            xaxis_title_standoff=25,  # Adjust standoff for X axis titles
            yaxis_title_standoff=25,  # Adjust standoff for Y axis titles
            hoversubplots = 'axis',
            hovermode = 'x unified',
            # hoverdistance = -1,
        )

        if show:
            fig.show()

        return fig


    @staticmethod
    def future_savings_house_plot(starting_point, savings_scenario_arr, house_scenario_arr, show = True):
        
        future_steps = np.arange(starting_point, starting_point + len(savings_scenario_arr), dtype = int)

        # Create figure with a single trace for each segment
        fig = go.Figure()

        # Add trace for the first segment (before color change point)
        fig.add_trace(go.Scatter(x=future_steps, y=savings_scenario_arr, name='ETF Savings scenario', line=dict(color='blue'), stackgroup = 'one'))

        # Add trace for the second segment (after color change point)
        fig.add_trace(go.Scatter(x=future_steps, y=house_scenario_arr, name='House + ETF savings scenario.', line=dict(color='red'), stackgroup = 'two'))


        # Update layout
        fig.update_layout(
            title='Line Plot with Color Change',
            xaxis_title='X Axis',
            yaxis_title='Y Axis',
            height=600,  # Adjust height of the figure
            width=1200,   # Adjust width of the figure 

            title_x=0.5,    # Set title position to the middle horizontally
            title_y=0.95,   # Set title position closer to the top vertically
            xaxis_title_standoff=25,  # Adjust standoff for X axis titles
            yaxis_title_standoff=25,  # Adjust standoff for Y axis titles
            hoversubplots = 'axis',
            hovermode = 'x unified',
        )

        if show:
            # Show plot
            fig.show()
        
        return fig


