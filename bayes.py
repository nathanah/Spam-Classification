import numpy as np
import random


priorMemo = 0

def readFile():
    #import data
    file = "spambase.data"

    file = open(file, 'r')
    data = file.read()
    data = data.split('\n')
    data.pop(len(data)-1)

    #Split each sample into its features and read as correct data type
    for i in range(len(data)):
        #Split features
        data[i] = data[i].split(",")

        #Cast each feature
        for j in range(57):
            data[i][j] = float(data[i][j])

        #Read in class label as it, since it's 1/0
        data[i][57] = int(data[i][57])

    data = np.array(data)

    #Bucket using simple quantiles
    #bucket(2, data)

    #Shuffle data:
    np.random.shuffle(data)

    #Split X and Y
    x = data[:,:57]
    y = data[:,57]
    return [x, y]


"""
    Bayes nets usually work on discrete values, not continuous variables.
    This function transforms the continuous values of our data into discrete buckets with labels.

    Params:
        buckets: the number of buckets we are dividing the data into (quantiles)
        data: the entire set of data before it has been split into X and Y

    Side-effect:
        data is transformed and no longer the same as before it was passed in
"""
def bucket(buckets, data):

    #Go through each column except for the label
    for i in range(57):

        #Sort the data on the given column
        data = data[np.argsort(data[:, i])]

        #Variable to store the lower bound of the current quantile
        lower = 0

        #Go through each quantile labeling it with the proper bucket
        for j in range(buckets):

            #Get the upper cutoff of the current quantile.
            upper = (j+1) * (len(data) / buckets)
            upper = int(upper)

            #Label all samples in range with current bucket
            data[lower:upper, i] = j

            #Upper cutoff becomes lower bound.
            lower = upper

"""
    Bucketing method that classify a feature into 1/0 depend which mean it is closer to.
    Isolated calculating the averages to only the training set.
    This we are not using the testing set to label certain values as correlated to spam or not.
    This can be thought of using K-means for k=2 on each feature separately.
    We calculate the center of that feature for each class, and label which class the sample belongs to for that feature.

    Param:
        trainingX: Our set of samples for training
        trainingY: Our set of labels for training
        testingX: Our set of samples to be used for verifying
        testingY: Our set of labels to be use for verifying

    Process;
        1. Pass through each feature calculating the spam/not-spam means
        2. Replace value of the feature for its class label
"""
def bucket_closerMean(trainingX, trainingY, testingX, testingY):

    # Go through each feature (i,j) = (feature, sample)
    # date[sample, feature] = data[j, i]
    for i in range(57):

        #Count number of spam/not-spam samples
        count_spam = 0
        count_notSpam = 0

        #Store summed value of each feature
        sum_spam = 0
        sum_nonSpam = 0

        #Store mean of each feature (center of cluster)
        mean_spam = 0
        mean_nonSpam = 0

        #Sum up the value of the feature, counting labels for spam/not-spam
        #Looks only at the training set so it doesn't make assumptions on the testing set
        for j in range(len(trainingX)):
            if trainingY[j] == 1:
                count_spam += 1
                sum_spam += trainingX[j][i]
            else:
                count_notSpam += 1
                sum_nonSpam += trainingX[j][i]

        #Calculate the mean
        mean_spam = sum_spam / count_spam
        mean_nonSpam = sum_nonSpam / count_notSpam

        #Reassign values for the training set
        for j in range(len(trainingX)):
            if abs(trainingX[j][i] - mean_spam) > abs(trainingX[j][i] - mean_nonSpam):
                trainingX[j][i] = 0
            else:
                trainingX[j][i] = 1

        #Reassign values for the testing set using the training set
        for j in range(len(testingX)):
            if abs(testingX[j][i] - mean_spam) > abs(testingX[j][i] - mean_nonSpam):
                testingX[j][i] = 0
            else:
                testingX[j][i] = 1

"""
    Prior is defined as the probability of any sample being in the class.
    We can calculate this by just counting up the number of samples that are spam.
    P(not spam) = (1 - P(spam))

    Params:
        y: the labels for all of our data

    Returns:
        Probability of any sample being spam (the prior)
"""
def prior(Y):

    spam = 0

    for i in range(len(Y)):
        if Y[i] == 1:
            spam += 1

    prior = spam / len(Y)
    return prior

"""
    Likelihood is the probability P(xj | spam/not-spam)
    We can calculate this by looking looking at the number of elements in that class that have the certain feature we are looking for.

    That is: (count of v in c) / (total number of samples in c)

    Params:
        x: our set of all samples X
        y: our set of all labels Y
        j: the column we are looking at
        v: the value we are looking for in the column
        c: what class we are looking at

    Returns:
        P(xj | spam/not-spam)
"""
def likelihood():

    memory = np.zeros(shape=(2, 57), dtype="object")
    print(memory)

    def inner(X, Y, j, v, c):

        #Memory is formatted as:
        #memory[class][feature] stores an array [[value, probability], [value, probabliity]] pairs.

        #No values stored for that class and feature pair
        if(memory[c][j] == 0):
            memory[c][j] = []

        index = 0

        #See if value is in the memo
        for i in range(len(memory[c][j])):
            if(memory[c][j][i][0] == v):
                index = i
                break

        #No pairs stored or no matching pair was found
        #we need to calculate likelihood and store
        if(len(memory[c][j]) == 0 or memory[c][j][index][0] != v):

            #Count of occurences of that value
            count = 0

            #Total count of that class
            total = 0

            #Iterate through each sample
            for i in range(len(X)):

                #If the classes are the same update total number of that class
                if Y[i] == c :
                    total +=1

                    #If the values match update our count of value
                    if(X[i][j] == v):
                        count += 1

            likelihood = count / total

            memory[c][j].append([v, likelihood])

            return likelihood

        else:
            #print("Memory hit for (c,j,v): (",c,j,v,")")
            zzz = 2


        #Otherwise return the stored value
        return memory[c][j][index][1]

    return inner

"""
    Posterior is the probability P(Spam | x). We calculate this with Bayes theroem. And by doing a trick of P(Spam | X) / P(!Spam | X) and seeing if it is >= 1.

    Params:
        x: our set of all samples X to train from
        y: our set of all labels Y to train from
        s: the sample we are looking at
        prior: the prior probabliity of a sample being spam
"""
def posterior(X, Y, s, prior, likelihood_func):

    #Get the probability that it is spam
    numerator = prior

    #Go through each feature and calculate likelihood, multiplying it
    for j in range(57):
        v = s[j]
        numerator *= likelihood_func(X, Y, j, v, 1)

    #Get the probability that it is not spam
    denominator = 1 - prior

    #Go through each feature and calculate likelihood, multiplying it
    for j in range(57):
        v = s[j]
        denominator *= likelihood_func(X, Y, j, v, 0)

    #Fix divide by zero by adding 1 to top and bottom. Still maintains ratio.
    return ( 1 + numerator) / (1 + denominator)

def test(trainingX, trainingY, testingX, testingY):

    #Track spam statistics
    TP = 0
    TN = 0
    FP = 0
    FN = 0

    p = prior(trainingY)

    likelihood_func = likelihood()

    print("Calculated prior:", p)

    #Go through each sample
    for i in range(len(testingX)):
        predict = posterior(trainingX, trainingY, testingX[i], p, likelihood_func)

        #If the prediction is >= it is spam
        if(predict >= 1):

            #If the sample is spam, guessed correctly (TP)
            if(testingY[i] == 1):
                TP += 1
            #If the sample is not spam, guessed wrong (FP)
            else:
                FP += 1
        #If the prediction is < 1 it is not spam
        else:

            #If the sample is spam, guessed incorrectly (FN)
            if(testingY[i] == 1):
                FN += 1
            #If the sample is not spam, guessed correctly (TN)
            else:
                TN += 1

    print("TP:", TP)
    print("TN:", TN)
    print("FP:", FP)
    print("FN:", FN)
    print("Accuracy", (TN + TP) / (TN + TP + FP + FN))

def main():

    #Read in data and preprocess it
    data = readFile()
    x = data[0]
    y = data[1]
    print("Finished preprocessing.")

    #Portion of samples to be used for training:
    split = .66
    cutoff = int(split * len(x))

    #Split training and Testing sets
    trainingX = x[:cutoff]
    trainingY = y[:cutoff]
    testingX = x[cutoff:]
    testingY = y[cutoff:]

    #Using Ethan's method transform the testing data based on the training data only.
    bucket_closerMean(trainingX, trainingY, testingX, testingY)

    test(trainingX, trainingY, testingX, testingY)

main()