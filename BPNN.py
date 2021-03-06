#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import openpyxl
import numpy as np
from torch.utils import data
import torch
from d2l import torch as d2l
from torch import nn
from numpy.random import permutation
import pandas as pd
import random
import numpy as np
from sklearn.utils import shuffle
import sklearn
import scipy.stats as stats
from sklearn import preprocessing


# In[20]:


fpath = "D:\\OA_残值预测档案\\中汽研二手车数据\\feature_1020.xlsx"
DataSet = pd.read_excel(fpath, engine='openpyxl')
print(DataSet.head(5))


# In[3]:


def Outlier_Delete(DataSet, Series_name ,t_stud=3):
    '''
    按照正态分布的末端值去除离群点
    Input：DataFrame DataSet ； 针对对象列； t-student 的值，一般取3，可调整正常值范围
    Output：用该对象列去除离群点后的数据集
    '''
    DataSet = DataSet.sort_values(by=Series_name)
    mean = DataSet[Series_name].mean()
    sigma = DataSet[Series_name].std()
    # 筛选异常值
    DataSet_new = DataSet.loc[( mean-t_stud*sigma < DataSet[Series_name]) & (DataSet[Series_name]  < mean+t_stud*sigma) , :]
    return DataSet_new


# In[21]:


DataSet_new = Outlier_Delete(DataSet, '新车指导价', 1)
# 以新车指导价对样本进行去噪，留下大概只有指导价150w以内的样本
DataSet_new2 = Outlier_Delete(DataSet_new, '车龄', 2)
# 以车龄对样本进行去噪，留下大概只有19年以内的样本
DataSet_new3 = Outlier_Delete(DataSet_new2, '过户次数', 6)
# 以过户次数对样本进行去噪，留下大概只有指导价5次以内的样本
DataSet = Outlier_Delete(DataSet_new3, '平均里程', 4)
# 以平均里程数对样本进行去噪，留下大概只有指导价5次以内的样本
# 以上留下多少，用Outlier_Delete最后一个参数可调整

DataSet = shuffle(DataSet)#将整个数据集重新随机排列


# In[22]:


# hyperparameter setting:
TrainRatio = 4/5
ValiRatio = 1/5

nData = len(DataSet)
nTrain = TrainRatio * nData
nVali = ValiRatio * nData
train_data = DataSet.iloc[0:int(nTrain)]
test_data =DataSet.iloc[int(nTrain):nData]
# test_data =DataSet[nTrain+nVali:-1]
guideprice_test = test_data['新车指导价'].values


# testset的新车指导价
# preprocess
all_features = pd.concat((train_data.iloc[:, 0:-1], test_data.iloc[:, 0:-1]))
print(all_features)


# In[23]:


# process numerical variable
# normalization
numeric_features = all_features.dtypes[all_features.dtypes != 'object'].index
# feature为数值的列索引, 注意object即为字符串类型
all_features[numeric_features] = all_features[numeric_features].apply(
    lambda x: (x - x.mean()) / (x.std()))
# 在标准化数据之后均值为0，因此我们可以将缺失值设置为0（均值）
all_features[numeric_features] = all_features[numeric_features].fillna(0)
# process discrete variable
all_features = pd.get_dummies(all_features, dummy_na=True)
# One-hot code
# `Dummy_na=True` 将“na”（缺失值）视为有效的特征值，并为其创建指示符特征。


# In[7]:


np.shape(all_features)[1]


# In[24]:


x_train = all_features.iloc[0:int(nTrain)].values
x_test = all_features.iloc[int(nTrain):].values
y_train=torch.tensor(train_data['交易价格'].values)
y_test=torch.tensor(test_data['交易价格'].values)


# In[9]:


#BPNN



import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
import tf_slim as slim
import numpy as np
from sklearn.metrics import accuracy_score
from tensorflow.keras import backend




class BPNN(object):
    def __init__(self,input_n,hidden_n,output_n,lambd):
        """
        这是BP神经网络类的构造函数
        :param input_n:输入层神经元个数
        :param hidden_n: 隐藏层神经元个数
        :param output_n: 输出层神经元个数
        :param lambd: 正则化系数
        """
        self.Train_Data = tf.placeholder(tf.float64,shape=(None,input_n),name='input_dataset')                                  # 训练数据集
        self.Train_Label = tf.placeholder(tf.float64,shape=(None,output_n),name='input_labels')                                 # 训练数据集标签
        self.input_n = input_n                                                                                                    # 输入层神经元个数
        self.hidden_n = hidden_n                                                                                                  # 隐含层神经元个数
        self.output_n = output_n                                                                                                  # 输出层神经元个数
        self.lambd = lambd   # 正则化系数
        self.input_weights = tf.Variable(tf.random_normal((self.input_n, self.hidden_n),mean=0,stddev=1,dtype=tf.float64),trainable=True)                                       # 输入层与隐含层之间的权重
        self.hidden_weights =  tf.Variable(tf.random_normal((self.hidden_n,self.output_n),mean=0,stddev=1,dtype=tf.float64),trainable=True)                                      # 隐含层与输出层之间的权重
        self.hidden_threshold = tf.Variable(tf.random_normal((1,self.hidden_n),mean=0,stddev=1,dtype=tf.float64),trainable=True)                                            # 隐含层的阈值
        self.output_threshold = tf.Variable(tf.random_normal((1,self.output_n),mean=0,stddev=1,dtype=tf.float64),trainable=True)                                            # 输出层的阈值
        # 将层与层之间的权重与偏置项加入损失集合
        
        tf.add_to_collection('loss', tf.keras.regularizers.l2(self.lambd)(self.input_weights))
        tf.add_to_collection('loss', tf.keras.regularizers.l2(self.lambd)(self.hidden_weights))
        tf.add_to_collection('loss', tf.keras.regularizers.l2(self.lambd)(self.hidden_threshold))
        tf.add_to_collection('loss', tf.keras.regularizers.l2(self.lambd)(self.output_threshold))
        # 定义前向传播过程
        self.hidden_cells = tf.sigmoid(tf.matmul(self.Train_Data,self.input_weights)+self.hidden_threshold)
        self.output_cells = tf.sigmoid(tf.matmul(self.hidden_cells,self.hidden_weights)+self.output_threshold)
        # 定义损失函数,并加入损失集合
        self.MSE = tf.reduce_mean(tf.square(self.output_cells-self.Train_Label))
        tf.add_to_collection('loss',self.MSE)
        # 定义损失函数,均方误差加入L2正则化
        self.loss = tf.add_n(tf.get_collection('loss'))

    def train_test(self,Train_Data,Train_Label,Test_Data,Test_Label,learn_rate,epoch,iteration,batch_size):
        """
        这是BP神经网络的训练函数
        :param Train_Data: 训练数据集
        :param Train_Label: 训练数据集标签
        :param Test_Data: 测试数据集
        :param Test_Label: 测试数据集标签
        :param learn_rate:  学习率
        :param epoch:  时期数
        :param iteration: 一个epoch的迭代次数
        :param batch_size:  小批量样本规模
        """
        train_loss = []                 # 训练损失
        test_loss = []                  # 测试损失
        test_accarucy = []              # 测试精度
        test_result = []
        with tf.Session() as sess:
            datasize = len(Train_Label)
            self.train_step = tf.train.GradientDescentOptimizer(learn_rate).minimize(self.loss)
            sess.run(tf.global_variables_initializer())
            for e in np.arange(epoch):
                for i in range(iteration):
                    start = (i*batch_size)%datasize
                    end = np.min([start+batch_size,datasize])
                    sess.run(self.train_step,
                             feed_dict={self.Train_Data:Train_Data[start:end],self.Train_Label:Train_Label[start:end]})
                    if i % 10000 == 0:
                        total_MSE = sess.run(self.MSE,
                                             feed_dict={self.Train_Data:Train_Data,self.Train_Label:Train_Label})
                        print("第%d个epoch中，%d次迭代后，训练MSE为:%g"%(e+1,i+10000,total_MSE))
                # 训练损失
                _train_loss = sess.run(self.MSE,feed_dict={self.Train_Data:Train_Data,self.Train_Label:Train_Label})
                train_loss.append(_train_loss)
                # 测试损失
                _test_loss = sess.run(self.MSE, feed_dict={self.Train_Data:Test_Data, self.Train_Label: Test_Label})
                test_loss.append(_test_loss)
                # 测试精度
                test_result = sess.run(self.output_cells,feed_dict={self.Train_Data:Test_Data})
                test_accarucy.append(self.Accuracy(test_result,Test_Label))
        return train_loss,test_loss,test_accarucy,test_result

    def Accuracy(self,test_result,test_label):
        """
        这是BP神经网络的测试函数
        :param test_result: 测试集预测结果
        :param test_label: 测试集真实标签
        """
        predict_ans = []
        label = []
        for (test,_label) in zip(test_result,test_label):
            test = np.exp(test)
            test = test/np.sum(test)
            predict_ans.append(np.argmax(test))
            label.append(np.argmax(_label))
        return accuracy_score(label,predict_ans)


# In[10]:


input_n = np.shape(all_features)[1]
output_n = 1
hidden_n = int(np.sqrt(input_n*output_n))
lambd = 0.001
batch_size = 500
learn_rate = 0.001
epoch = 50
iteration = 10000

    # 训练并测试网络
bpnn = BPNN(input_n,hidden_n,output_n,lambd)
train_loss,test_loss,test_accuracy,test_result = bpnn.train_test(x_train,y_train,x_test,y_test,learn_rate,epoch,iteration,batch_size)
Trade_price = pd.DataFrame(y_test) # trade price
Guide_price = pd.DataFrame(guideprice_test) #guide price
Pred_price = pd.DataFrame(test_result) # prediction price
data = pd.concat((Pred_price,Trade_price,Guide_price), axis = 1)


# In[16]:


print(data)


# In[17]:


apath = "D:\\feature_12081.csv"
data.to_csv(apath,sep=',',index=True,header=True)


# In[ ]:




