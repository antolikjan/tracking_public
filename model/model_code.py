import pandas
import pickle
import torch
import torch.nn as nn
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
import argparse
import wandb
import plotly.express as px
import plotly.graph_objs as go
import numpy
import numpy.ma as ma
from sklearn.preprocessing import StandardScaler

# TODO
# 3. make a parametric sweep for the sparsness metaparameter

class MyDataset(Dataset): 
  """
  relationships_to_ignore - An NxN boolean matrix where N is number of features in the dataset. 
  The relationships marked with True will be ignored in training. 
  """

  def __init__(self,train=True,relationships_to_ignore=None, dataset=None,metadata=None):
    #f = open('model\cache.pickle','rb')

    #d = pickle.load(f)
    self.data = dataset#d[0]
    self.md = metadata#d[1]
    todel = [col for col in self.data.columns if self.md['Units'].loc[col] == 'string']
    d = self.data.drop(columns=todel)

    # rescale data to 0-1 range
    scaler = StandardScaler()
    d = pandas.DataFrame(scaler.fit_transform(d),columns=d.columns)

    # remove columns that have least that 5% of data (the resit is NaNs)
    missing_ratio = d.isnull().mean()
    columns_to_keep = missing_ratio[missing_ratio <= 0.95].index
    # identify columns that were deleted
    columns_deleted = [col for col in d.columns if col not in columns_to_keep]
    print("Columns deleted due to having >95% NaNs:")
    print(columns_deleted)
    d = d[columns_to_keep]

    # add bias column
    d['bias']=1.0

    #determine dimensionality of our dataset
    self.dim = d.shape[1]

    #retrieve relationships to ignore
    self.relationships_to_ignore = torch.zeros((self.dim,self.dim), dtype=torch.bool) if relationships_to_ignore==None else torch.tensor(relationships_to_ignore.astype('bool'))

    # remove trivial relationships - based on very high correlation without delay
    correlation_matrix = d.corr()
    self.relationships_to_ignore = self.relationships_to_ignore | torch.tensor(numpy.abs(correlation_matrix.values) > 0.9, dtype=torch.bool)

    # print out the removed relationships
    removed_column_pairs = []
    column_names = d.columns
    for i in range(self.relationships_to_ignore.shape[0]):
        for j in range(i+1, self.relationships_to_ignore.shape[1]):
            # If the entry is True, add the column pair to the list
            if self.relationships_to_ignore[i,j]:
                removed_column_pairs.append((column_names[i], column_names[j]))

    # Print column pairs
    print('Following relationships were removed as they were deemed to be trivial due to very high same-day correlation (>0.9):')
    print(str(len(removed_column_pairs)) + " (" + str(len(removed_column_pairs)/(self.dim*self.dim)*100)+ "%)" + " of relationships have been removed.")

    for pair in removed_column_pairs:
        print(pair) 

    # sepperate into training and validation dataset
    if train:
       self.data_withnan = d[:-20].astype('float32')
    else:
       self.data_withnan = d[-20:].astype('float32')
    
    # replace NaNs with the mean of each column
    self.data = self.data_withnan.fillna(self.data_withnan.mean().fillna(0))
    
  def __len__(self):
    return len(self.data.index)
     
  def __getitem__(self,idx):
    return torch.tensor(self.data.iloc[idx].values),torch.tensor(self.data_withnan.iloc[idx].values)
  
class JanModel(nn.Module):
    def __init__(self, size):
        super().__init__()
        self.alphas = nn.Parameter(torch.rand(size)) #change it to a prior of your choice (currently initialised to values between 0 and 1)
        self.Ws = nn.Parameter(torch.rand(size, size)) #change it to a prior of your choice (currently initialised to values between 0 and 1)

    def forward(self, A,B):
        al = torch.special.expit(self.alphas)
        B = al * B + (1-al) * A
        B.detach()
        self.Ws.data.fill_diagonal_(0)
        pred = torch.matmul(B,self.Ws)
        return pred,B

def run_model(df,md):
  print('hello STARTING')
  config = {
    "epochs" : 2000, #povodne: 2000
    "lr" : 30*2e-5,
    "sparsness" : 0.003,
  }

  wandb.init(project="self-tracking-ml-new",config=config)

  training_data = MyDataset(dataset=df,metadata=md)
  validation_data = MyDataset(train=False,dataset=df,metadata=md) #mozno aj tu: dataset=df,metadata=md
  train_dataloader = DataLoader(training_data, batch_size=1, shuffle=False)
  validation_dataloader = DataLoader(validation_data, batch_size=1, shuffle=False)
    
  model = JanModel(size=len(training_data.data.columns))
  wandb.watch(model, log_freq=300)


  # # simple training loop (dataloader has to be implemented)
  optimizer = torch.optim.Adam(model.parameters(), lr=wandb.config['lr'])
  # zero out weights corresponding to relationships we want to ignore
  model.Ws.data = model.Ws.data * (~ training_data.relationships_to_ignore)

  for i in range(0,wandb.config['epochs']):
      # print('Epoch: ' + str(i))
      B = torch.zeros(len(training_data.data.columns))
      w_grad_tmp = torch.zeros(model.Ws.shape)
      a_grad_tmp = torch.zeros(model.alphas.shape)
      for data in train_dataloader:
          At, At_with_nan = data
          # for missing data fill in the predictions so that we give better estimation of B
          #At_pred, _ = model(At,B.detach())
          #mask = numpy.isnan(At_with_nan) * ~ numpy.isnan(At_pred.detach())
          #V = At.clone().detach()
          #V[mask]=At_pred.clone().detach()[mask]
          #At = V
          
          # run the actual forward step for optimization 
          At_pred, B = model(At,B.detach())

          # LOSS
          acc_loss = torch.mean((At - At_pred)**2) # accuracy
          sparsity_loss = torch.norm(model.Ws,p=1) #sparsity
          loss = acc_loss + float(i)/wandb.config['epochs']*wandb.config['sparsness']*sparsity_loss   
          loss.backward()
          
          # zero out gradient of Ws where data is missing
          nan_indices_alt = torch.nonzero(torch.isnan(At_with_nan)[0]).flatten()
          model.Ws.grad[:,nan_indices_alt] = w_grad_tmp[:,nan_indices_alt]
          model.alphas.grad[nan_indices_alt] = a_grad_tmp[nan_indices_alt]
          w_grad_tmp = model.Ws.grad.clone().detach()
          a_grad_tmp = model.alphas.grad.clone().detach()

          # zero out gradients where we want to ignore relationships
          model.Ws.grad = model.Ws.grad * (~ training_data.relationships_to_ignore)

      optimizer.step()
      optimizer.zero_grad()

    
      if i % 20 == 0:
        print('Epoch: ' + str(i))
        plt1 = px.histogram(torch.flatten(model.Ws.detach()))
        plt2 = go.Figure(go.Heatmap(z=model.Ws.detach().numpy(),x=training_data.data.columns,y=training_data.data.columns,colorscale='Viridis'))
        plt3 = go.Figure(go.Heatmap(z=model.alphas.detach().numpy().reshape(-1,1),x=["a"],y=training_data.data.columns,colorscale='Viridis'))
        wandb.log({'weights' : plt2, 'weight_dist' : plt1, 'alphas' : plt3, 'percent_above_0.01' : torch.mean(torch.flatten(model.Ws.detach())>0.01,dtype=float)*100})
        #show_plot(model_page_reference, model,training_data,i)

      val_err=0
      y = []
      y_est = []
      for data in validation_dataloader:
          At, At_with_nan = data
          At_pred, B = model(At,B.detach())
          val_err += torch.mean((At - At_pred)**2)
          y.append(At_with_nan.numpy())
          y_est.append(At_pred.detach().numpy())

      y=numpy.array(numpy.squeeze(y)).T
      y_est=numpy.array(numpy.squeeze(y_est)).T
      corrs = [ma.corrcoef(ma.masked_invalid(y[i]),ma.masked_invalid(y_est[i]))[0][1] for i in range(len(y))]
      corrs = numpy.nan_to_num(corrs,0)
      
      wandb.run.summary["final_corr"] = numpy.mean(corrs)
      wandb.log({"total_loss": loss, "accuracy_loss" : acc_loss, "sparsity_loss" : sparsity_loss,'val_err' : val_err/len(validation_data),'val_corr' : numpy.mean(corrs)})

  corrs_df = pandas.DataFrame([corrs,torch.special.expit(model.alphas.detach()).numpy()], columns=validation_data.data.columns)
  new_column_df = pandas.DataFrame({'name': ['corrs','alphas']})
  result = pandas.concat([new_column_df,corrs_df], axis=1)
  wandb.log({ 'performance_table' : result})

  torch.set_printoptions(threshold=10_000)
  numpy.set_printoptions(threshold=10_000)

  weights_result=model.Ws
#   weigths_converted_to_array=weights_result.detach().numpy()
#   print(f"Weights: {weigths_converted_to_array}")

  alphas_result = model.alphas
#   alphas_result_converted_to_array=alphas_result.detach().numpy()
#   print(f"Alphas: {alphas_result_converted_to_array}")
  return training_data.data.columns, weights_result, alphas_result


