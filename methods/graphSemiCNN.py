import keras.layers.convolutional as conv
import keras.layers.pooling as pool
import keras.regularizers as reg
from keras.layers import Input, Dropout, Activation, Flatten, Dense, Concatenate, Reshape
from keras.layers.merge import Dot
from keras.models import Model
from keras.optimizers import SGD # stochastic gradient descent

"""
Semi-supervised learning with convolution neural network
"""
class GraphSemiCNN: 
    def build(self, nb_genes, nb_classes):
        # params
        dropout_f = 0.25 # prevent overfitting
        dropout_c = 0.25
        dropout_d = 0.25

        # feature extration
        nb_filters = 500
        kernel_size = 10
        L1CNN = 0
        actfun = 'relu'
        pool_size = 11 # window size for features
        
        # hidden layers
        units1 = 200 # number of nodes in hidden layer
        units2 = 150
        units3 = 120
        units4 = 100

        # compilation
        INIT_LR = 0.01 # initial learning rate
        lamb = 1.0

        # build the model
        input1 = Input(shape=(nb_genes, 1))
        feature1 = conv.Conv1D(nb_filters, kernel_size, padding='same', kernel_initializer='he_normal', 
                kernel_regularizer=reg.l1(L1CNN))(input1)
        feature1 = Dropout(dropout_f)(feature1)
        feature1 = Activation(actfun)(feature1)
        feature1 = pool.MaxPooling1D(pool_size)(feature1)
        feature1 = Flatten()(feature1)

        input2 = Input(shape=(nb_genes, 1))
        feature2 = conv.Conv1D(nb_filters, kernel_size, padding='same', kernel_initializer='he_normal', 
                kernel_regularizer=reg.l1(L1CNN))(input2)
        feature2 = Dropout(dropout_f)(feature2)
        feature2 = Activation(actfun)(feature2)
        feature2 = pool.MaxPooling1D(pool_size)(feature2)
        feature2 = Flatten()(feature2)
        
        hidden1_1 = Dense(units1, activation='relu')(feature1)
        target = Dense(units3, activation='relu')(hidden1_1) # z1 -> z3
        hidden1_2 = Dense(units1, activation='relu')(feature2)
        context = Dense(units3, activation='relu')(hidden1_2)
        hidden2 = Dense(units2, activation='relu')(hidden1_1) # z1 -> z2
        hidden4 = Dense(units4, activation='relu')(target) # z3 -> z4
        concatenated = Concatenate(axis=1)([hidden2, hidden4]) # concatenate z2, z4
        concatenated = Dropout(dropout_c)(concatenated)

        similarity = Dot(axes=1, normalize=True)([target, context]) # setup for the validation model
        dot_product = Dot(axes=1)([target, context])
        dot_product = Reshape((1,))(dot_product)
        dot_product = Dropout(dropout_d)(dot_product)
        
        output1 = Dense(nb_classes, activation='softmax', name='output1')(concatenated)
        output2 = Dense(1, activation='sigmoid', name='output2')(dot_product)

        model = Model(inputs=[input1, input2], outputs=[output1, output2], name='graphSemiCNN')
        val_model = Model(inputs=[input1, input2], outputs=similarity) # similarity callback

        # compile the model
        losses = {
            'output1': 'categorical_crossentropy',
            'output2': 'binary_crossentropy',
        }
        lossWeights = {'output1': 1.0, 'output2': lamb}
        opt = SGD(lr=INIT_LR)      
        model.compile(loss=losses, loss_weights=lossWeights, optimizer=opt, metrics=['accuracy']) # loss function: cross entropy
        
        return model, val_model

