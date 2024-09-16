#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Set up
## Configs
from os import getcwd
from os.path import join 

## visualisation
import pandas as pd 
import matplotlib.pyplot as plt
import hvplot.pandas #monkey patch for pandas --> upgrades plots 
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

## data manipulation 
import numpy as np 
from itertools import product

## sampling 
import random 

## wallet which have done more than 100 actions
def sample_more_naction(df, wallet_or_proposal, no):
    
    """
    Goals: Sample proposal that have done more than n actions 
    
    Inputs:
    - df = data frame to sample form
    - wallet_or_proposal = if true then wallet else (string of wallet or porposal) 
    - no = threshold no of actions (integer)
    
    Outputs:
    - wallet addresses with top or bottom most average funds
    
    """
    sub_sample = df.groupby(wallet_or_proposal).count()
    sub_sample = sub_sample[sub_sample['action']>no].reset_index()
    sub_sample = sub_sample[wallet_or_proposal]
    
    return list(sub_sample) 
    
sample_more_naction(df_pi, 'wallet', 50)
    


def sample_wallet_by_action(df, action, portion_of_wallets=0.3, ascending=True):
    
    """
    Goals: Sample for wallet by action 
    
    Inputs:
    - df = data frame to sample form
    - action = action of evaluation (string)
    - pop_pct = percentage of population to sample from (float between 0 to 1)
    - ascending = ascending show bottom x%, vice versa (Bolean)
    
    Outputs:
    - proposal addresses with top or bottom most average funds
    
    """

    ### action per wallet 
    sub_sample = df_pi.groupby(['wallet', 'action']).count().reset_index()

    ### sort frequency by action pay in descending order 
    sub_sample = sub_sample[sub_sample['action']==action].sort_values('proposal', ascending=ascending)

    ### take top x% of wallets 
    n_wallet = int(sub_sample.shape[0]*portion_of_wallets) 

    ## sample wallet 
    sub_sample = sub_sample[:n_wallet]['wallet']
    
    return list(sub_sample) 

sample_wallet_by_action(df_pi, 'pay', 0.3, ascending=True)




def sample_proposal_success(df, portion_of_wallets=0.3, unsuccessful=True):
    
    """
    Goals: Sample for most successful proposal
    
    Inputs:
    - df = data frame to sample form
    - portion_of_wallets = proportion of population to sample from (float between 0 to 1)
    - successful = If true show top x%, vice versa (Bolean)
    
    Outputs:
    - proposal addresses with top or bottom most average funds
    
    """
    
    ### action per wallet 
    sub_sample = df.groupby(['proposal']).mean().reset_index()

    ### sort frequency by action pay in descending order 
    sub_sample = sub_sample.sort_values('proposal_funds', ascending=unsuccessful)

    ### take top x% of proposals
    n_proposal = int(sub_sample.shape[0]*portion_of_wallets) 

    ## sample wallet 
    sub_sample = sub_sample[:n_proposal]['proposal'].unique()
    
    return list(sub_sample)

sample_proposal_success(df_pi, 0.3, unsuccessful=True)


# In[10]:


# Q1: Which actions does each wallet perform on each proposal?

def sampled_graph_action_of_wallet_on_proposal(dataframe, sqrt_sample_size=3, nmin_threshold_actions=50):
    

    ## set df 
    df = dataframe[dataframe['action']!='initialize'].groupby(['wallet','proposal', 'action']).count().reset_index()

    ## number of visualisation 
    N=sqrt_sample_size

    ## no_of_action samples 
    sub_sample = sample_more_naction(dataframe, 'wallet', nmin_threshold_actions) # return list of wallets which have complete more than n min threshold of actions
    sample_wallets = random.sample(sub_sample, N**2)

    ## colourcode 
    colors=dict(zip(df.action.unique(),['red', 'green', 'yellow', 'blue', 'cyan', 'brown']))

    ## determine position of output
    pos = list(product(range(1,(1+N)), range(1,(1+N))))

    # set up fig & populate 
    fig = make_subplots(rows=N, 
                        cols=N, 
                        horizontal_spacing=0.05,
                        vertical_spacing=0.05,
                        shared_xaxes=True,
                        y_title='Frequency', 
                        x_title='',
                        subplot_titles=sample_wallets)

    # create a figure 
    for pos_df in zip(pos, sample_wallets):

        pos, w_id = pos_df

        r, c = pos 

        for a in df.action.unique(): 

            ## select sub df 
            data=df[(df['wallet']==w_id) & (df['action']==a)].to_dict('series')

            # add figures 
            fig.add_trace(
                        go.Bar(
                        name=a,
                        legendgroup=a, #one legend for all 
                        x=data['proposal'],
                        y=data['timestep'], # remember this is just a count 
                        showlegend=False,
                        marker_color=colors[a]
                        ),

                        row=r, col=c
                    )  



    fig.update_layout(barmode='stack',
                      height=900, 
                      width=900, 
                      coloraxis=dict(colorscale='RdBu'),
                      font=dict(size=8),
                      title_text=f"Actions performed by each wallet on each proposal [Sampled: {N**2} Wallets]")




    ## change size and colour of subtitles 
    for i in fig['layout']['annotations']:
        i['font'] = dict(size=8,color='#000000')

    fig.show()


# ## Dimensions: Proposals, Action, Time 
# 
# - Q1: How do the actions performed on each proposal change over time?
# - Q2: How does the frequency of each action change over time?
# - Q3: How are proposals performing over time?
# - Q4: Which actions are being performed on each proposal?
# 

# In[11]:

def sampled_graph_action_on_proposal(dataframe, sqrt_sample_size=3, portion_of_wallets=0.3, unsuccessful=True):

    ## set df 
    df = dataframe.groupby(['proposal','timestep', 'action']).count().reset_index()

    ## number of visualisation 
    N  = sqrt_sample_size

    ## random samples 
    sub_sample = sample_proposal_success(df, portion_of_wallets=portion_of_wallets, unsuccessful=unsuccessful)
    sample_proposals = random.sample(sub_sample, N**2)

    ## colourcode 
    colors =dict(zip(df.action.unique(),['red', 'green', 'yellow', 'blue', 'cyan', 'brown']))

    ## showledgend switch 
    showlegend=True 


    ## determine position of output
    pos = list(product(range(1,(1+N)), range(1,(1+N))))

    # set up fig & populate 
    fig = make_subplots(rows=N, 
                        cols=N, 
    #                     shared_xaxes='all',
    #                     shared_yaxes='all',
                        horizontal_spacing=0.05,
                        vertical_spacing=0.05,
                        y_title='Frequency', 
                        x_title='Timestep',
                        subplot_titles=sample_proposals)

    # create a figure 
    for pos_df in zip(pos, sample_proposals):

        pos, p_id = pos_df

        r, c = pos 

        for a in df.action.unique(): 

            ## select sub df 
            data=df[(df['proposal']==p_id) & (df['action']==a)].to_dict('series')

            # add figures 
            fig.add_trace(
                        go.Bar(
                        name=a,
                        legendgroup=a, #one legend for all 
                        x=data['timestep'],
                        y=data['wallet'],
                        showlegend=False,
                        marker_color=colors[a]
                        ),

                        row=r, col=c
                    )  

        #showlegend=False 


    fig.update_layout(barmode='stack',
                      height=900, 
                      width=900, 
                      coloraxis=dict(colorscale='RdBu'),
                      showlegend=True,
    #                   title_pad={'b':0, 'l':0, 'r':0, 't':0}, 
                      title_text= f"Actions performed on each proposal over time [Sampled: {N**2} Wallets]")

    # fig.update_xaxes(title='timestep',title_font_size=8)
    # fig.update_yaxes(title='frequency',title_font_size=8) #does not amend size



    ## change size and colour of subtitles 
    for i in fig['layout']['annotations']:
        i['font'] = dict(size=8,color='#000000')

    fig.show()




# In[12]:


# Q2: How does the frequency of each action change over time?

def frequency_of_each_action_on_proposal(dataframe):
    """
    Goal: Show frequency of each action over time
    """
    
    fig_df = dataframe.groupby(['timestep', 'action' ]).count().reset_index()
    fig_df
    fig = px.line(
        fig_df,
        x='timestep',
        y='proposal',
        color='action',
        title='Actions performed on proposals over time',
        labels={"timestep": "Timestep",
                "proposal": "Frequency",             
                "action": "Action",             
               })

    fig.show()
    


# In[13]:


# Q3: How are proposals performing over time?

def performance_of_proposal_over_time(dataframe):
    fig_df = dataframe.groupby(['timestep', 'proposal' ]).sum().reset_index()

    fig = px.line(
        fig_df,
        x='timestep',
        y='proposal_funds',
        color='proposal',
        title='Performance of proposals over time',
        labels={"timestep": "Timestep",
                "proposal": "Frequency",             
                "proposal_funds": "Proposal Funds",             
               })

    fig.show()

# In[14]:


def sampled_graph_action_on_proposal(dataframe, sqrt_sample_size=3, nmin_threshold_actions=50):
    

    ## set df 
    df = dataframe.groupby(['proposal', 'action']).count().reset_index()

    ## number of visualisation 
    N=sqrt_sample_size

    ## no_of_action samples 
    sub_sample = sample_more_naction(dataframe, 'proposal', nmin_threshold_actions) # return list of proposal which have complete more than n min threshold of actions
    sample_proposals = random.sample(sub_sample, N**2)

    ## colourcode 
    colors=dict(zip(df.action.unique(),['red', 'green', 'yellow', 'blue', 'cyan', 'brown']))

    ## determine position of output
    pos = list(product(range(1,(1+N)), range(1,(1+N))))

    # set up fig & populate 
    fig = make_subplots(rows=N, 
                        cols=N, 
                        horizontal_spacing=0.05,
                        vertical_spacing=0.05,
                        shared_xaxes=False,
                        y_title='Frequency', 
                        x_title='Proposal',
                        subplot_titles=sample_proposals)

    # create a figure 
    for pos_df in zip(pos, sample_proposals):

        pos, p_id = pos_df

        r, c = pos 

        for a in df.action.unique(): 

            ## select sub df 
            data=df[(df['proposal']==p_id) & (df['action']==a)].to_dict('series')

            # add figures 
            fig.add_trace(
                        go.Bar(
                        name=a,
                        legendgroup=a, #one legend for all 
                        x=data['proposal'],
                        y=data['timestep'], # remember this is just a count 
                        showlegend=False,
                        marker_color=colors[a]
                        ),

                        row=r, col=c
                    )  



    fig.update_layout(barmode='group',
                      height=900, 
                      width=900, 
                      coloraxis=dict(colorscale='RdBu'),
                      font=dict(size=8),
                      title_text=f"Actions performed by each wallet on each proposal [Sampled: {N**2} Wallets]")




    ## change size and colour of subtitles 
    for i in fig['layout']['annotations']:
        i['font'] = dict(size=8,color='#000000')

    fig.show()


# ## Dimension: Wallet, Action, Time 
# - Q1: Which actions does each wallet perform over time?
# - Q2: How does the frequency of each action change over time?
# - Q3: How does each wallet perform over time?
# - Q4: Which actions does each wallet perform?

# In[16]:


# Q1: Which actions does each wallet perform over time?
def sampled_graph_action_wallet_over_time(dataframe, sqrt_sample_size=3, nmin_threshold_actions=10):
    ## set df 
    df = dataframe.groupby(['wallet','timestep', 'action']).count().reset_index()

    ## number of visualisation 
    N=sqrt_sample_size

    ## random samples 
    sub_sample = sample_more_naction(dataframe, 'wallet', nmin_threshold_actions) # return list of wallets which have complete more than n min threshold of actions
    sample_wallets = random.sample(sub_sample, N**2)


    ## colourcode 
    colors =dict(zip(df.action.unique(),['red', 'green', 'yellow', 'blue', 'cyan', 'brown']))


    ## determine position of output
    pos = list(product(range(1,(1+N)), range(1,(1+N))))

    # set up fig & populate 
    fig = make_subplots(rows=N, 
                        cols=N, 
                        horizontal_spacing=0.05,
                        vertical_spacing=0.05,
                        y_title='Frequency', 
                        x_title='Timestep',
                        subplot_titles=sample_wallets)

    # create a figure 
    for pos_df in zip(pos, sample_wallets):

        pos, w_id = pos_df

        r, c = pos 

        for a in df.action.unique(): 

            ## select sub df 
            data=df[(df['wallet']==w_id) & (df['action']==a)].to_dict('series')

            # add figures 
            fig.add_trace(
                        go.Bar(
                        name=a,
                        legendgroup=a, #grouped legend 
                        x=data['timestep'],
                        y=data['proposal'],
                        showlegend=False,
                        marker_color=colors[a]
                        ),

                        row=r, col=c
                    )  


    fig.update_layout(barmode='stack',
                      height=900, 
                      width=900, 
                      coloraxis=dict(colorscale='RdBu'),
                      showlegend=True,
                      title_text="Actions performed on by each wallet over time [Sampled]")


    ## change size and colour of subtitles 
    for i in fig['layout']['annotations']:
        i['font'] = dict(size=8,color='#000000')

    fig.show()



# In[19]:


def sampled_graph_actions_of_wallet(dataframe, sqrt_sample_size=3, nmin_threshold_actions=50):
    

    ## set df 
    df = dataframe.groupby(['wallet', 'action' ]).count().reset_index()

    ## number of visualisation 
    N=sqrt_sample_size

    ## no_of_action samples 
    sub_sample = sample_more_naction(dataframe, 'wallet', nmin_threshold_actions) # return list of proposal which have complete more than n min threshold of actions
    sample_proposals = random.sample(sub_sample, N**2)

    ## colourcode 
    colors=dict(zip(df.action.unique(),['red', 'green', 'yellow', 'blue', 'cyan', 'brown']))

    ## determine position of output
    pos = list(product(range(1,(1+N)), range(1,(1+N))))

    # set up fig & populate 
    fig = make_subplots(rows=N, 
                        cols=N, 
                        horizontal_spacing=0.05,
                        vertical_spacing=0.05,
                        shared_xaxes=False,
                        y_title='Frequency', 
                        x_title='Wallet',
                        #subplot_titles=sample_proposals
                       )

    # create a figure 
    for pos_df in zip(pos, sample_proposals):

        pos, w_id = pos_df

        r, c = pos 

        for a in df.action.unique(): 

            ## select sub df 
            data=df[(df['wallet']== w_id) & (df['action']==a)].to_dict('series')

            # add figures 
            fig.add_trace(
                        go.Bar(
                        name=a,
                        legendgroup=a, #one legend for all 
                        x=data['wallet'],
                        y=data['timestep'], # remember this is just a count 
                        showlegend=False,
                        marker_color=colors[a]
                        ),

                        row=r, col=c
                    )  



    fig.update_layout(barmode='group',
                      height=900, 
                      width=900, 
                      coloraxis=dict(colorscale='RdBu'),
                      font=dict(size=8),
                      title_text=f"Actions performed by each wallet on each proposal [Sampled: {N**2} Wallets]")




    ## change size and colour of subtitles 
    for i in fig['layout']['annotations']:
        i['font'] = dict(size=8,color='#000000')

    fig.show()


# ## Dimension: Wallet, Proposal, Time 
# - Q1: What are the common characteristics between wallets that join or fund a proposal? Do they cluster? [Pending]
# - Q2: How does each wallet perform over time?
# - Q3: How does each proposal perform over time?
# - Q4: How do the wallet interactions with proposals change over time?

# In[17]:


# Q1: What are the common characteristics between wallets that join or fund a proposal? Do they cluster? [Pending]


# In[22]:


# Q2: How does each wallet perform over time?

def wallet_funds_over_time(dataframe):
    fig_df = dataframe.groupby(['timestep', 'wallet' ]).sum().reset_index()

    fig = px.line(
        fig_df,
        x='timestep',
        y='wallet_funds',
        color='wallet',
        title='Performance of wallets over time',
        labels={"timestep": "Timestep",
                "proposal": "Frequency",             
                "wallet_funds": "Wallet Funds",             
               })

    fig.show()

# In[25]:


# Q4: How do the wallet interactions with proposals change over time?

def df_action_over_time_by_type_of_action(dataframe):

    ## re-structure df 
    df_action_over_time = dataframe.groupby(['timestep', 'action']).count()['wallet']
    df_action_over_time = df_action_over_time.reset_index()



    fig = px.histogram(
        df_action_over_time,
        x='timestep',
        y='wallet',
        color='action',
        nbins=int(100/10),
        marginal="rug",
        title='Action of all Wallets over time by type of action',
        labels={"timestep": "Timestep",
                'wallet': 'No. of actions performed', 
                #'action': 'Action'

               })

    fig.show()
