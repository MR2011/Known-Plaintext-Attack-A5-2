# Known Plaintext Attack against A5/2
This project is the result of the course Cryptography Project at HTWSaar.
The attack was published by Goldberg, Wagner and Green in 1999 and is
explained by Barkan, Biham and Keller in [1].

## Installation
The dependencies are listed in the  [requirements.txt](./requirements.txt) file. To install all dependencies simply
execute the following command:
```
	pip install -r requirements.txt
```
## Run
The main program can be executed with:
```
	python3 main.py
```
You have the following options:

- Generate a keystream pair with A5/1
- Generate a keystream pair with A5/2
- Retrieve the session key for two given keystream pairs and their frame counters

If you want to execute the attack with given R4 (you need to specify the values in the main method), you can use:
```
	python3 gww_attack.py
```
Notice: The two frame counters must differ only in one bit such that F1 XOR F2 = 2048!
## Performance
The attack performance was tested on a regular desktop PC with an Intel Core i7-770K CPU, 16 GB DDR4 memory and Windows 10 as operating system. 
If the correct value of R4 is given, retrieving the session key is pretty quick and usually needs just a few seconds. 
Finding the correct value of R_4 is the expensive part of the attack. 
In the worst case, i.e., if the value of R4=2^17 the attacks needs around 3 hours, tested with 8 parallel processes. 

## Links
[1] Instant Ciphertext-Only Cryptanalysis of GSM Encrypted Communication 
http://www.cs.technion.ac.il/users/wwwb/cgi-bin/tr-get.cgi/2003/CS/CS-2003-05.pdf
