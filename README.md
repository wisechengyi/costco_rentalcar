# Costco Renter Car Accelerator
## Why
Costco car rental provides great value, e.g. free cancellations and no hidden fees, but the user experience can suck in that searching for rental cars is limited at 4 locations maximum at a time, so it would be annoying to find the best price around.

## Solution
```
pip install bs4 requests
python script.py
```
Sample output:
```
$ python script.py 
page 1: [93.0, 93.0, 93.0, 93.0, 93.0, 93.0, 93.0, 93.38, 93.38, 99.0, 99.0, 99.0, 99.0, 99.0, 99.0, 100.0, 100.0, 103.0, 103.0, 106.76] at (4, 8)
page 2: [50.0, 54.0, 58.59, 64.0, 71.0, 93.0, 93.0, 93.0, 93.0, 93.0, 93.38, 99.0, 99.0, 99.0, 99.0, 100.0, 100.0, 100.0, 103.0, 103.0] at (4, 8)
page 3: [48.57, 54.0, 55.0, 55.0, 55.0, 55.0, 58.0, 58.0, 58.0, 58.0, 58.0, 58.0, 62.0, 64.96, 68.0, 68.0, 69.0, 71.0, 75.0, 78.0] at (0, 4)
page 4: [48.35, 54.0, 55.0, 55.0, 55.0, 55.0, 56.0, 56.0, 58.0, 65.0, 65.99, 70.0, 72.0, 74.0, 76.0, 80.0, 80.0, 84.0, 84.0, 88.0] at (0, 4)
```
Then you know which page has the best deal, and go to the regular web page to complete your booking. 

TODO: Tell user which exact location has the best deal.

## Parameters
Currently parameters have to manually tailored to your needs with [this variable](https://github.com/wisechengyi/costco_rentalcar/blob/master/script.py#L179-L204).
