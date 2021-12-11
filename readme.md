# Readme

### Generating private and public keys:   
  `ssh-keygen -o -t rsa -b 4096 -e -m pem`   

### Converting publickey file to format acceptable in software:
  `ssh-keygen -f zaidchecker.pub -e -m pem > zaidchecker.pub.pem`

### Usage of the private key:
  Paste the privatekey file in the keygen folder.
### Usage of the public key:
  Paste the content of zaidchecker.pub.pem in the software.

### Generating Licence files:
  Provide the keygen with a valid email and it will generate a licence file.

### Unlocking the Software:
  Paste the licence file in the Software folder.