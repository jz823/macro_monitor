import pandas as pd
import numpy as np
import itertools
import datetime as dt
import plotly.graph_objects as go
import plotly.express as px

class macro_monitor:
    def __init__(self):
        self.csv_link_dict = {"cpi_lfe": "https://fred.stlouisfed.org/graph/fredgraph.csv?&id=CORESTICKM159SFRBATL",  # Sticky Price Consumer Index Less Food and Energy
                              "inflation_y5": "https://fred.stlouisfed.org/graph/fredgraph.csv?&id=T5YIE",   # 5-Year Breakeven Inflation Rate
                              "real_gdp": "https://fred.stlouisfed.org/graph/fredgraph.csv?&id=GDPC1",          # Real GDP
                              "real_gdp_pc": "https://fred.stlouisfed.org/graph/fredgraph.csv?&id=A939RX0Q048SBEA",  # Real Gross Domestic Product Per Capita
                              "sofr": "https://fred.stlouisfed.org/graph/fredgraph.csv?&id=SOFR",               # Secured Overnight Financing Rate (SOFR)
                              "tbill_yield_1m": "https://fred.stlouisfed.org/graph/fredgraph.csv?&id=DTB4WK",   # 4-Week Treasury Bill Secondary Market Rate, Discount Basis
                              "tbill_yield_3m": "https://fred.stlouisfed.org/graph/fredgraph.csv?&id=DTB3",     # 3-Month Treasury Bill Secondary Market Rate, Discount Basis
                              "tbill_yield_6m": "https://fred.stlouisfed.org/graph/fredgraph.csv?&id=DTB6",     # 6-Month Treasury Bill Secondary Market Rate, Discount Basis
                              "tbill_yield_1y": "https://fred.stlouisfed.org/graph/fredgraph.csv?&id=DTB1YR",   # 1-Year Treasury Bill Secondary Market Rate, Discount Basis
                              "tnote_yield_2y": "https://fred.stlouisfed.org/graph/fredgraph.csv?&id=DGS2",     # Market Yield on U.S. Treasury Securities at 2-Year Constant Maturity, Quoted on an Investment Basis
                              "tnote_yield_5y": "https://fred.stlouisfed.org/graph/fredgraph.csv?&id=DGS5",     # Market Yield on U.S. Treasury Securities at 5-Year Constant Maturity, Quoted on an Investment Basis
                              "tnote_yield_7y": "https://fred.stlouisfed.org/graph/fredgraph.csv?&id=DGS7",     # Market Yield on U.S. Treasury Securities at 7-Year Constant Maturity, Quoted on an Investment Basis
                              "tnote_yield_10y": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10",   # Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity, Quoted on an Investment Basis
                              "tnote_yield_20y": "https://fred.stlouisfed.org/graph/fredgraph.csv?&id=DGS20",   # Market Yield on U.S. Treasury Securities at 20-Year Constant Maturity, Quoted on an Investment Basis
                              "tnote_yield_30y": "https://fred.stlouisfed.org/graph/fredgraph.csv?&id=DGS30"    # Market Yield on U.S. Treasury Securities at 30-Year Constant Maturity, Quoted on an Investment Basis
        }
        self.yield_curve = {"sofr":1/360,
                            "tbill_yield_1m":1/12,
                            "tbill_yield_3m":3/12,
                            "tbill_yield_6m":6/12,
                            "tbill_yield_1y":1,
                            "tnote_yield_2y":2,
                            "tnote_yield_5y":5,
                            "tnote_yield_7y":7,
                            "tnote_yield_10y":10,
                            "tnote_yield_20y":20,
                            "tnote_yield_30y":30}
        
    def get_indicators(self):
        for ind in self.csv_link_dict:
            print(ind)

    def get_dataset(self,indicators:list[str],start_date=None,end_date=None,date_col_name='DATE',date_col_format='%Y-%m-%d'):
        df = pd.DataFrame()
        for ind in indicators:
            id_string = self.csv_link_dict[ind].split('=')[1]
            df_get = pd.read_csv(self.csv_link_dict[ind]).rename(columns={date_col_name:'DATE',id_string:ind})
            df_get['DATE'] = df_get['DATE'].astype(str)
            df_get['DATE'] = df_get['DATE'].apply(lambda dt_str: dt.datetime.strptime(dt_str,date_col_format))
            df_get.set_index('DATE',inplace=True,drop=True)
            df = pd.merge(df,df_get,how='outer',left_index=True,right_index=True)
        if (start_date is None) and (end_date is None):
            return df
        elif (start_date is not None) and (end_date is not None):
            df = df.loc[(df.index >= start_date) & (df.index <= end_date)]
        elif (start_date is not None):
            df = df.loc[df.index >= start_date]
        else:
            df = df.loc[df.index <= end_date]
        return df

    def get_2d_curves(self,df,fill_na=False):
        df = df.apply(pd.to_numeric, errors='coerce')
        if fill_na:
            df = df.fillna(method='ffill')
        data = []
        for ind in df.columns:
            data.append(go.Scatter(x=df.index,y=df[ind],mode='lines',name=ind,connectgaps=True))
        fig = go.Figure(data=data)
        fig.update_layout(xaxis_title='time',
                          yaxis_title='rate/data',
                          title='Time Series of ' + ','.join(df.columns))
        fig.update_xaxes(type='date')
        return fig
    
    def get_yield_curve_data(self,start_date=None,end_date=None,date_col_name='DATE',date_col_format='%Y-%m-%d'):
        return self.get_dataset(self.yield_curve,start_date,end_date,date_col_name,date_col_format)
    
    def get_yield_curve_3d(self,df,fill_na=False):
        df = df.apply(pd.to_numeric, errors='coerce')
        if fill_na:
            df = df.fillna(method='ffill')
        df = df.rename(columns=self.yield_curve)
        xx = df.index
        yy = df.columns
        xy = itertools.product(df.index,df.columns)
        zz = map(lambda ele:df.loc[ele[0]][ele[1]],xy)
        zz = np.array(list(zz)).reshape(len(xx),len(yy)).T
        xx,yy = np.meshgrid(xx,yy)


        trace = go.Surface(x=xx,y=yy,z=zz)
        layout = go.Layout(width=1000,height=1000,hovermode='x',scene=dict(xaxis_title='date',yaxis_title='maturity',zaxis_title='rate'))
        fig = go.Figure(data=[trace],layout=layout)

        return fig
    
    def get_yield_curve_2d(self,df,sample_dates:list[dt.datetime],fill_na=False):
        sample_dates.sort()
        df = df.rename(columns=self.yield_curve)
        if fill_na:
            df = df.fillna(method='ffill')
        df = df.apply(pd.to_numeric, errors='coerce')
        #print(df)
        data = []
        for sample_date in sample_dates:
            if sample_date not in df.index:
                print(f'Date {sample_date} not available.')
                continue
            #print(sample_date)
            #print(df.loc[sample_date].values)
            #print(df.columns)
            data.append(go.Scatter(x=df.columns,y=df.loc[sample_date].values,mode='lines',name=f'Yield Curve {sample_date.date()}',connectgaps=True))
        if data == []:
            print('All the dates unavailable.')
            return
        fig = go.Figure(data=data)
        fig.update_layout(xaxis_title='maturity',
                          yaxis_title='rate',
                          title='Time Series on ' + ','.join(map(lambda x: dt.datetime.strftime(x,"%Y-%m-%d"),sample_dates)))
        return fig
    
    def get_latest_yield_curve(self,date_col_name='DATE',date_col_format='%Y-%m-%d',fill_na=False):
        df = self.get_dataset(self.yield_curve,date_col_name='DATE',date_col_format="%Y-%m-%d")
        cur_day = dt.datetime.combine(dt.datetime.today().date(),dt.time())
        while (cur_day not in df.index):
            cur_day -= dt.timedelta(days=1)
            # print(cur_day)
        else:
            # print(df.loc[cur_day])
            return self.get_yield_curve_2d(df,[cur_day],fill_na)
