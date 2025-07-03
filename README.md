# FAKE CALLS


## Geração dos datasets
```
$ export GOOGLE_API_KEY=<google_maps_key>
$ python get_ref_points.py
$ python make_address_descriptions.py
$ python main.py 400
$ python fix_missing_infos.py
```