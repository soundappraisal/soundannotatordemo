The soundannotatordemo repository provides democode accompanying the libsoundannotator
repository, available from https://github.com/soundappraisal/libsoundannotator.
The library libsoundannotator is designed for processing sound using
time-frequency representations.

The democode implements the two scenarios illustrated in our white paper:
    * 'Time-frequency or time-scale representation fission and fusion rules', Coen Jonker, Arryon D. Tijsma, Ronald A.J. van Elburg available from Arxiv.org.

The scientific underpinning for the main signal processing algorithms can be found in:
    * 'Texture features for the reproduction of the perceptual organization of sound', Ronald A.J. van Elburg and Tjeerd C. Andringa  available from Arxiv.org.
    
The democode provides two use cases: UseCase-ProcessingFiles and UseCase-MicrophoneAtADistance. Both scripts start with the code and at the end they contain a block with parameters. We advice to study the block with parameters carefully before using the scripts.

In addition the projects folder contains two scripts with which one can achieve similar results as with the UseCase scripts by setting the correct input arguments. The input arguments can be found by passing --help flag when running these scripts.    

We hope to improve the documentation over time, for now we hope you find the softare usefull as is.
