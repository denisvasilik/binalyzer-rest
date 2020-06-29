"""
    binalyzer_rest.rest
    ~~~~~~~~~~~~~~~~~~~

    CLI extension for the *binalyzer* command.
"""
import click
import sys
import ssl
import os
import logging

from werkzeug.serving import run_simple
from werkzeug.utils import import_string
from flask._compat import text_type

from .rest import flask_app


class CertParamType(click.ParamType):
    """Click option type for the ``--cert`` option. Allows either an
    existing file, the string ``'adhoc'``, or an import for a
    :class:`~ssl.SSLContext` object.
    """

    name = 'path'

    def __init__(self):
        self.path_type = click.Path(
            exists=True, dir_okay=False, resolve_path=True)

    def convert(self, value, param, ctx):
        try:
            return self.path_type(value, param, ctx)
        except click.BadParameter:
            value = click.STRING(value, param, ctx).lower()

            if value == 'adhoc':
                try:
                    import OpenSSL
                except ImportError:
                    raise click.BadParameter(
                        'Using ad-hoc certificates requires pyOpenSSL.',
                        ctx, param)

                return value

            obj = import_string(value, silent=True)

            if sys.version_info < (2, 7, 9):
                if obj:
                    return obj
            else:
                if isinstance(obj, ssl.SSLContext):
                    return obj

            raise

def _validate_key(ctx, param, value):
    """The ``--key`` option must be specified when ``--cert`` is a file.
    Modifies the ``cert`` param to be a ``(cert, key)`` pair if needed.
    """
    cert = ctx.params.get('cert')
    is_adhoc = cert == 'adhoc'

    if sys.version_info < (2, 7, 9):
        is_context = cert and not isinstance(cert, (text_type, bytes))
    else:
        is_context = isinstance(cert, ssl.SSLContext)

    if value is not None:
        if is_adhoc:
            raise click.BadParameter(
                'When "--cert" is "adhoc", "--key" is not used.',
                ctx, param)

        if is_context:
            raise click.BadParameter(
                'When "--cert" is an SSLContext object, "--key is not used.',
                ctx, param)

        if not cert:
            raise click.BadParameter(
                '"--cert" must also be specified.',
                ctx, param)

        ctx.params['cert'] = cert, value

    else:
        if cert and not (is_adhoc or is_context):
            raise click.BadParameter(
                'Required when using "--cert".',
                ctx, param)

    return value

def show_server_banner(env, debug):
    """Show extra startup messages the first time the server is run,
    ignoring the reloader.
    """
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        return

    click.echo(' * Environment: {0}'.format(env))

    if debug is not None:
        click.echo(' * Debug mode: {0}'.format('on' if debug else 'off'))


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
    """Run a local test server. The reloader and debugger are enabled by default if
    BINALYZER_ENV=development or BINALYZER_DEBUG=1.
    """
    show_server_banner('production', False)

    run_simple(host,
               port,
               flask_app,
               use_reloader=reload,
               use_debugger=None,
               threaded=with_threads,
               ssl_context=cert)
