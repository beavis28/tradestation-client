# tradestation-client

Python client for [Tradestation's API](https://tradestation.github.io/api-docs/) 🐍

This project is nowhere-near completed and is a continual work-in-progress, this repo mainly exists to demonstrate to the world that I can indeed write code 😁

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
    login_secrets={
        "What was the make or model of your first car?": {
            "QuestionId": "99",
            "SecurityAnswer": "Bugatti Veyron",
        },
        "What is your mother's maiden name?": {
            "QuestionId": "77",
            "SecurityAnswer": "Smith",
        },
        "What is the name of your first pet?": {
            "QuestionId": "33",
            "SecurityAnswer": "Rover"
        }
    }
)

ts.get_quotes('MSFT')[0]['Last'] # 212.20
```

## Contributing

Please open a new issue if you wish to contribute to this project. 

## Authors

* [Sam Bragg](github.com/sambragg)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

