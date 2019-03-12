import matplotlib
matplotlib.use('Agg')

import argparse
from methods.utils import load_data, sample_training_set, plot_loss_acc
from sklearn.preprocessing import LabelBinarizer
from methods.graphSemiCNN import GraphSemiCNN
import progressbar
from methods.callbacks import similarity_callback
from sklearn.metrics import classification_report
import pickle

def main():
    parser = argparse.ArgumentParser(description="This script is for training the semi-supervised neural network model")
    parser.add_argument('-e', '--exp', required=True, help='path to input gene expression data, with genes in rows and samples in columns')
    parser.add_argument('-l', '--label', required=True, help='path to input labels')
    parser.add_argument('-m', '--model', required=True, help='path to output trained model')
    parser.add_argument('-b', '--label_bin', required=True, help='path to output label binarizer')
    parser.add_argement('-p', '--plot', required=True, help='path to output accuracy/loss plot')
    parser.add_argement('-c', '--epochs', default=75, type=int, help='number of epochs to train for')
    args = parser.parse_args()

    # params
    exp_path = args.exp
    label_path = args.label
    model_path = args.model
    label_bin_path = args.label_bin
    plot_path = args.plot
    nb_epochs = args.epochs
    
    nb_neighbors = 2
    sample_size = 10000
    batch_size = 32

    # load data, shuffle the samples, and scale data
    print('[INFO] loading training data...')
    dat = load_data(exp_path, label_path)

    # construct the KNN graph, sample context distribution, and split the data (60% trn; 20% val; 20% tst)
    trn, val, tst = sample_training_set(dat, sample_size)
    
    # one-hot encoding
    lb = LabelBinarizer()
    lb.fit(dat['out']) # labels
    trn['out'][0] = lb.transform(trn['out'][0])
    val['out'][0] = lb.transform(val['out'][0])
    tst['out'][0] = lb.transform(tst['out'][0])
    nb_classes = len(lb.classes_) # note: training classes vs data classes

    # build and train the model
    print('[INFO] building and training the model...')
    nb_samples = trn['inp'][0].shape[0]
    nb_genes = trn['inp'][0].shape[1]
    model, val_model = GraphSemiCNN().build(nb_genes, nb_classes)
    
    history = {}
    ind = np.arange(nb_samples)
    ind_list = [ind[i * batch_size:(i + 1) * batch_size] for i in range((len(ind) + batch_size - 1) // batch_size)]
    for e in range(nb_epochs):
        bar = progressbar.ProgressBar()
        for i in bar(range(100)):
            for j in len(ind_list):
                trainX = [trn['inp'][0][ind_list[j]], trn['inp'][1][ind_list[j]]]
                trainY = [trn['out'][0][ind_list[j]], trn['out'][1][ind_list[j]]]
                validX = [val['inp'][0][ind_list[j]], val['inp'][1][ind_list[j]]]
                validY = [val['out'][0][ind_list[j]], val['out'][1][ind_list[j]]]
                loss = model.train_on_batch(trainX, trainY)
                val_loss = model.evaluate(validX, validY)
            history_callback()
            similarity_callback(val, dat, val_model)

    # loss = loss[0]
    # acc = loss[1]
    # val_loss = val_loss[0]
    # val_acc = val_loss[1]
    history['loss'] = loss
    history['val_loss'] = val_loss

    fit_history = model.fit(inp['train'], out['train'], validation_data=(inp['valid'], out['valid']), 
            epochs=nb_epochs, batch_size=batch_size, callbacks=[histories, similarities]) 

    # evaluate the model
    print('[INFO] evaluating the model...')
    predictions = model.predict(inp['test'], batch_size=batch_size)
    print(classification_report(out['test'][0].argmax(axis=1),
	predictions[0].argmax(axis=1), target_names=lb.classes_))

    # plot the training loss and accuracy
    plot_loss_acc(plot_path, nb_epochs, fit_history)

    # save the model and label binarizer
    print('[INFO] serializing the model and label binarizer...')
    model.save(model_path)
    f = open(label_bin_path, 'wb')
    f.write(pickle.dumps(lb))
    f.close()

if __name__ == "__main__":
    main()

