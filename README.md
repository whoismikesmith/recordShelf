# recordShelf

A light-based tool to visualize information about vinyl record collections. The system is meant for you to browse a digital list of records, select one, and have an indicator LED nearest the desired record blink to help you find it's location.

## Getting Started

This flask app will start a local web server which will attempt to download a public Discogs user's entire collection to a local json file. You can then browse the collection, filtering it by various criteriea or searching via text input, and make a selection to be indicated by an LED on the actual shelf.

### Prerequisites

We will use Fadecandy and opc drive the LEDs

```
https://github.com/scanlime/fadecandy
```

We will use Flask for the web server/framework .

```
sudo pip install Flask
```

### Installing

Clone the repository to your local system.

```
git clone https://github.com/whoismikesmith/shelf
```

Navigate to the project folder

```
cd shelf
```

Edit config.py and set the variable discogsUsername to your Discogs username

```
discogsUsername = "REPLACE_WITH_YOUR_DISCOGS_USERNAME"
```

In a new terminal window, start the web server

```
python app.py
```

Enter this url into a browser

```
http://localhost:5000
```

You should get an error stating you need to download new data, click the link to start the download process.

```
Click here to load collection data
```

While the collection data is being downloaded from discogs, you should see information feeding back in the terminal window about what page of data is currently being downloaded. When the process finishes your browser should refresh with a success message. Click to return home.

```
Click to return home.
```

Installation complete! You should now be able to browse a local list of your Discogs record collection that will trigger LED animations on a fadecandy server corresponding to the records physical locaton.

## Deployment

You will have to edit variables for the number of LEDs in your setup if it differs from mine, as well as an offset to account for records only taking up a portion of your shelf. Will add this soon.

## Built With

* [Flask](http://flask.pocoo.org/) - The web framework used
* [Fadecandy](https://github.com/scanlime/fadecandy) - LED Driver
* [Discogs API v2](https://www.discogs.com/developers/) - Used to gather data about record collection

## Contributing

I would love some help/criticism/feedback, I'm new to collaborative coding.

## Authors

* **Mike Smith** - *Initial work* - [whoismikesmith](https://github.com/whoismikesmith)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* scanlime for the amazing Fadecandy!
