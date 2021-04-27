"""
    binalyzer_rest.rest
    ~~~~~~~~~~~~~~~~~~~

    CLI extension for the *binalyzer* command.

    :copyright: 2021 Denis Vasilík
    :license: MIT, see LICENSE for details.
"""
import click

from werkzeug.serving import run_simple
from flask.cli import (
    CertParamType,
    _validate_key,
    show_server_banner,
)

from .rest import flask_app


@click.command()
@click.option('--host', '-h', default='0.0.0.0',
              help='The interface to bind to.')
@click.option('--port', '-p', default=8000,
              help='The port to bind to.')
@click.option('--cert', type=CertParamType(),
              help='Specify a certificate file to use HTTPS.')
@click.option('--key',
              type=click.Path(exists=True, dir_okay=False, resolve_path=True),
              callback=_validate_key, expose_value=False,
              help='The key file to use when specifying a certificate.')
@click.option('--reload/--no-reload', default=None,
              help='Enable or disable the reloader. By default the reloader '
              'is active if debug is enabled.')
@click.option('--debugger/--no-debugger', default=None,
              help='Enable or disable the debugger. By default the debugger '
              'is active if debug is enabled.')
@click.option('--with-threads/--without-threads', default=True,
              help='Enable or disable multithreading.')
def rest(host, port, reload, debugger, with_threads, cert):
    """Run a local server (experimental).
    """
    show_server_banner('production', False)

    run_simple(host,
               port,
               flask_app,
               use_reloader=reload,
               use_debugger=None,
               threaded=with_threads,
               ssl_context=cert)
