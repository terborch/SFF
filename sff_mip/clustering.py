""" This module contans functions related to clustering weather data using a
    k-means algorythm.
"""

# import pandas as pd
import matplotlib.pyplot as plt
# from datetime import datetime, timedelta
import numpy as np
# import os.path
# import json


import data

S, S_meta = data.get_param('settings.csv')
# Non clustered parameters
filename = 'meteo_Liebensberg_10min.csv'
epsilon = 1e-6
D, H = 365, 24
Days = list(range(D))
Hours = list(range(H))
Ext_T, Irradiance, Index = data.weather_param(
    filename, epsilon, (Days, Hours), S['Time'])


###############################################################################
### Normalize data
###############################################################################
import sklearn
# Scale the array to be clustered (not normalize)
from sklearn.preprocessing import scale 
# Cluster a 2D array using the k-means algorythm
from sklearn import cluster
# Identify the typical day in a given cluster
from sklearn.metrics import pairwise_distances_argmin_min
from sklearn.metrics import mean_squared_error


def norm(array):
    """ Returns the normalized version of a given array. Works with a 2D array. 
    """
    return (array - np.min(array))/(np.max(array) - np.min(array))

Ext_T_norm = norm(Ext_T)
Irradiance_norm = norm(Irradiance)

Data_norm = np.zeros((D, H*2))
for d in Days:
    Data_norm[d] = np.concatenate((Ext_T_norm[d], Irradiance_norm[d]), axis=0)

Data = np.zeros((D, H*2))
for d in Days:
    Data[d] = np.concatenate((Ext_T[d], Irradiance[d]), axis=0)
    
plt.plot(range(H*2), Data_norm[151,:])

def cluster_by_Kmeans(data, nbr_clusters, tol=1e-9, 
                      n_init=1e4, n_jobs=8, max_iter=1e9):
    """ Recieve data in the shape of (nbr_data_points, nbr_features)
    and a number of clusters. Use the scale methode form sklearn to
    scale the data. Use the KMeans method to cluster the data.
    Returns an array of cluster labels for each data point and 
    an array of the dtata points closest to the centroids. 
    """
    data_scaled = scale(data)
    compute_kmeans = cluster.KMeans(n_clusters=nbr_clusters)
    compute_kmeans.fit(data_scaled)
    labels, centers = compute_kmeans.labels_, compute_kmeans.cluster_centers_
    
    closest, _ = pairwise_distances_argmin_min(centers, data_scaled)

    return labels.tolist(), closest.tolist()

def cluster_0_to_365(Ext_T, Irradiance, start, stop, plot=True)
    import time
    cluster_start = time.time()
    
    Closest, Labels = np.zeros((D+1, D)), np.zeros((D+1, D))
    for c in range(2,D+1):
        labels, closest = cluster_by_Kmeans(Data_norm, c)
        Closest[c,:c] = closest
        Labels[c] = labels
    
    cluster_end = time.time()
    print('model construct time: ', cluster_end - cluster_start, 's')
    
    
    MSE = np.zeros(D+1)
    for c in range(2,D+1):
        MSE[c] = mse(Labels[c], Closest[c], norm(Ext_T), norm(Irradiance))
    start= 2
    plt.plot(range(len(MSE[start:])), MSE[start:])
    plt.plot(range(len(MSE[start:])), [0]*len(MSE[start:]), c='black', ls='--')
    plt.title('Clustering accuracy')
    plt.xlabel('Number of clusters')
    plt.ylabel('Mean Square error')
    plt.show()

def plot_clustered_data(Hours, Days, Ext_T, Irradiance, labels, closest):
    """ Plot each typical day relative to measured values for Temperature and
        Irradiance according to measurment and clustering values.
    """
    # clustered_days[Cluster][Days][0: Ext_t, 1: Irradiance][Hours]
    clustered_days = {}
    for d in Days:
        typical_period = labels[d]
        try:
            _ = clustered_days[typical_period]
        except:
            clustered_days[typical_period] = []
        clustered_days[typical_period].append([Ext_T[d], Irradiance[d]])

    for i in set(labels):
        fig, ax1 = plt.subplots()
        plt.title('External parameter clusters')
        ax1.set_xlabel('Hours')
        ax1.set_ylabel('Temperature in °C')
        ax2 = ax1.twinx()
        ax2.set_ylabel('Global Irradiance in kW/m^2')
        for d in range(len(clustered_days[i])):

            ax1.plot(Hours, clustered_days[i][d][0], 
                     label=f'Typical day nbr {i}', c='blue')
            ax2.plot(Hours, clustered_days[i][d][1], 
                     label=f'Typical day nbr {i}', c='red')
            print('i=', i)
            ax1.plot(Hours, Ext_T[int(closest[i])], 
                     label=f'Typical day nbr {i}', c='lightblue', linewidth=5)
            ax2.plot(Hours, Irradiance[int(closest[i])], 
                     label=f'Typical day nbr {i}', c='orange', linewidth=5)


# plot_clustered_data(Hours, Days, Ext_T, Irradiance, Labels[-1], Closest[-1])



def mse(labels, closest, Ext_T, Irradiance):
    
    y_predict, y_measured = np.zeros((D, H*2)), np.zeros((D, H*2))
    for d in Days:
        y_measured[d] = np.concatenate((Ext_T[d], Irradiance[d]), axis=0)
        
    for d in Days:
        d_type = int(closest[int(labels[d])])
        y_predict[d] = np.concatenate([Ext_T[d_type], Irradiance[d_type]])

    return mean_squared_error(y_measured, y_predict)



import pandas as pd


# K, C = 1000, [10, 20, 30, 50, 100]
# MSE = np.zeros((len(C), K))
# CLS = {'labels': {}, 'closest': {}} 
# for i, c in enumerate(C):
#     CLS['labels'][c] = np.zeros((K,D))
#     CLS['closest'][c] = np.zeros((K,c))
#     for k in range(K):
#         labels, closest = cluster_by_Kmeans(Data_norm, c)
#         MSE[i, k] = mse(labels, closest, norm(Ext_T), norm(Irradiance))
#         CLS['labels'][c][k] = labels
#         CLS['closest'][c][k] = closest
#     print(i)

Minimas = list(np.argmin(MSE, axis=1))
for k in range(K):
    plt.scatter(C, MSE[:,k], c='black') 
plt.scatter(C, [MSE[i,Minimas[i]] for i in range(len(C))], c='black', 
            label='Any iteration')    
plt.scatter(C, [MSE[i,Minimas[i]] for i in range(len(C))], c='red',
            label='Best iteration for a given nbr of clusters')
plt.title('Clustering accuracy - 1000 iterations')
plt.xlabel('Number of clusters')
plt.ylabel('Mean Square error')
plt.ylim(0.001,0.007)
plt.xticks(C)
plt.legend()
plt.show()  

import os
path = os.path.join('inputs', 'clsuters.h5')
for i, k in enumerate(Minimas):
    Cluster = np.concatenate((CLS['labels'][C[i]][k], CLS['closest'][C[i]][k]))
    data.save_to_hdf(f'Cluster_{C[i]}', Cluster, path)

# for n in range(0,30):
#     labels, closest = {}, {}
#     for c in range(2, 20):
#         labels[c], closest[c] = cluster_by_Kmeans(X, c)
    
#     json_dict = {'labels': labels, 'closest': closest}
#     with open(os.path.join('jsons', f'clusters_5_{n}.json'), 'w') as json_file:
#         json.dump(json_dict, json_file)


plt.plot(range(D*H), Ext_T.flatten())



