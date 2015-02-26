import sys, os
sys.path.insert(1, "../../../")
import h2o

def deeplearning_multi(ip, port):
    h2o.init(ip, port)

    print("Test checks if Deep Learning works fine with a multiclass training and test dataset")

    prostate = h2o.import_frame("smalldata/logreg/prostate.csv")

    hh = h2o.deeplearning(x             = prostate[0:2],
                          y             = prostate[4],
                          validation_x  = prostate[0:2],
                          validation_y  = prostate[4])
    hh.show()

if __name__ == '__main__':
    h2o.run_test(argv, deeplearning_multi)