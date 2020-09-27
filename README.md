# tradestation-client

Python client for [Tradestation's API](https://tradestation.github.io/api-docs/) 🐍

This project is nowhere-near completed and is a continual work-in-progress!

## Features

* Tradestation WebAPI:
  * Oauth token fetching & refreshing
  * Last price quotes
  * List account orders
  * List account positions
* Account transactions API 
  * Compatible with new 2FA requirements - September 2020
  * Automated scraping of each account's transactions for a given date

---

## Getting Started

### Prerequisites

This project uses `pipenv` to manage dependencies. If you don't have it installed, run: 

```
pip install pipenv
```

### Installing

Install all of  the required dependencies:

```
pipenv install
```

### Usage

```python
from tradestation-client import Tradestation

ts = Tradestation(
    client_id= 'foo',
    client_secret= 'bar',
    username='baz',
    password='hunter2',
    otp_secret='MY32BITSECRET'
)

ts.get_quotes('MSFT')[0]['Last'] # 212.20
```

## Contributing

Please open a new issue if you wish to contribute to this project. 

## Authors

* [Sam Bragg](https://github.com/sambragg)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

