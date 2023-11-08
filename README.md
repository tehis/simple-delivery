# Simple Delivery

This is a food delivery application.

To use this project, install the dependencies via:

```sh
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```


## APIs

There is three apis:

- annouce-delay/  -- request data: order_id: int
- delay-queue/    -- request data: agent_id: int  response: DelayQueue
- delay-report/   --           --                 response: Vendor and total_delay 

## Tests

To run tests, run this command:

```sh
pytest .
```

## Postman

![image](https://github.com/tehis/simple-delivery/assets/43639641/7bc4ea8a-1a30-456c-8077-dac89c388d51)


![image](https://github.com/tehis/simple-delivery/assets/43639641/d2e7167d-4330-473f-876e-935b8c3f0aab)


![image](https://github.com/tehis/simple-delivery/assets/43639641/62d8cdb3-a846-4c70-9ac9-96441a396857)


