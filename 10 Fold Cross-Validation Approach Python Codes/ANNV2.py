#library addition
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.wrappers.scikit_learn import KerasClassifier
from sklearn.model_selection import cross_validate, cross_val_predict

#data read
clinicalInput = pd.read_excel("..../")

#determine the number of classes(labels)
label_encoder = LabelEncoder().fit(clinicalInput.Label)
labels = label_encoder.transform(clinicalInput.Label)
classes = list(label_encoder.classes_)

#data preparation
clinicalOutput = clinicalInput["Label"]
clinicalInput = clinicalInput.drop(["Patient ID", "Patient age quantile","Label"],axis=1)

#determine number of features and classes
nb_features = 18
nb_classes = len(classes)

#Standardization of train data
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler().fit(clinicalInput.values)
clinicalInput = scaler.transform(clinicalInput.values)

#Model generation
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Activation, Dense, BatchNormalization
from tensorflow.keras import layers

#Determine f1, recall and precision values
from keras import backend as K

def recall_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    recall = true_positives / (possible_positives + K.epsilon())
    return recall

def precision_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
    precision = true_positives / (predicted_positives + K.epsilon())
    return precision

def f1_m(y_true, y_pred):
    precision = precision_m(y_true, y_pred)
    recall = recall_m(y_true, y_pred)
    return 2*((precision*recall)/(precision+recall+K.epsilon()))

#Convert output to categorical data
from tensorflow.keras.utils import to_categorical
clinicalOutput = to_categorical(clinicalOutput)

#Create network
def create_network():
    network = Sequential()
    network.add(layers.Dense(32, activation="relu",  input_shape=(nb_features,)))
    network.add(layers.Dense(units=16, activation='relu'))
    network.add(layers.Dense(8, activation="relu"))
    network.add(BatchNormalization())
    network.add(Dense(nb_classes))  
    network.add(Activation("softmax"))
    network.summary()

    from tensorflow.keras.optimizers import SGD
    opt = SGD(lr=1e-3, decay=1e-5, momentum=0.3, nesterov=True)

    network.compile(loss="binary_crossentropy", optimizer = opt, metrics=["accuracy",f1_m,precision_m,recall_m])
    return network

neural_network = KerasClassifier(build_fn=create_network, 
                                 epochs=250)

from sklearn.preprocessing import LabelBinarizer
lb = LabelBinarizer()
clinicalOutput = np.array([number[0] for number in lb.fit_transform(clinicalOutput)])

#Determine the cross validated results
results = cross_validate(neural_network, clinicalInput, clinicalOutput,cv=10,scoring=("accuracy","f1","recall","precision"))

print("Accuracy result: ", results["test_accuracy"])
print("Recall result: ", results["test_recall"])
print("Precision result: ", results["test_precision"])
print("F1 result: ", results["test_f1"])

#Plot results
import matplotlib.pyplot as plt
plt.plot(results["test_accuracy"],color="c")
plt.plot(results["test_f1"],color="m")
plt.plot(results["test_recall"],color="y")
plt.plot(results["test_precision"],color="k")
plt.title("Model Information (ANN)")
plt.ylabel("Model Performance")
plt.xlabel("Number of Folds")
plt.legend(["Accuracy","F1-Score","Recall","Precision"], loc="lower right")
plt.show()

#Determien the prediction
y_pred = cross_val_predict(neural_network, clinicalInput, clinicalOutput, cv=10)

#Provide AUC score
from sklearn.metrics import roc_auc_score
print("Accuracy result: ", np.mean(results["test_accuracy"]))
print("Recall result: ", np.mean(results["test_recall"]))
print("Precision result: ", np.mean(results["test_precision"]))
print("F1 result: ", np.mean(results["test_f1"]))
print("ROC: ", roc_auc_score(clinicalOutput, y_pred))
