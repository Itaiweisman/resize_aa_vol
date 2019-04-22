# resize_aa_vol
byItai

## Usage 
```
./resize_rep.py -v <Volume Name> -s <Capacity to add in GiB>
```

## Parameters within script
Parameter | Description	| Example 
----------| ----------- | ------- 
box_a	| DNS Name of first box with A/A | ibox_siteA	
box_b	| DNS Name of second box with A/A | ibox_siteB
auth  | Authentication Tuple | ('user','password')
host  | ESXi host (will be changed to cluster with the next release) | ESX102
