from flask import jsonify, url_for

class APIException(Exception):
    """
    APIException is a custom exception class for handling API errors uniformly.
    
    Attributes:
        message (str): Human-readable description of the exception.
        status_code (int): HTTP status code to be returned. Default is 400.
        payload (dict): Additional data to be returned in the error. Default is None.
    """
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        super().__init__(self)
        self.message = message
        if status_code is not None:
            if isinstance(status_code, int) and (100 <= status_code <= 599):
                self.status_code = status_code
            else:
                raise ValueError("Invalid HTTP status code.")
        self.payload = payload

    def to_dict(self):
        """
        Convert the APIException to a dictionary.

        Returns:
            dict: A dictionary containing 'message' and additional payload if any.
        """
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)

def generate_sitemap(app):
    links = ['/admin/']
    for rule in app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            if "/admin/" not in url:
                links.append(url)

    links_html = "".join(["<li><a href='" + y + "'>" + y + "</a></li>" for y in links])
    return """
        <div style="text-align: center;">
        <h1>Welcome to your API</h1>
        <p>API HOST: <script>document.write('<input style="padding: 5px; width: 300px" type="text" value="'+window.location.href+'" />');</script></p>
        <p>Remember to specify a real endpoint path like: </p>
        <ul style="text-align: left;">"""+links_html+"</ul></div>"