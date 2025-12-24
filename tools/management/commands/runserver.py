"""
Custom runserver command - Development server uyarısını kaldırır.
"""
from django.contrib.staticfiles.management.commands.runserver import (
    Command as StaticFilesRunserverCommand,
)


class Command(StaticFilesRunserverCommand):
    """Runserver command without the development warning."""

    def run(self, **options):
        """Run the server without printing the warning message."""
        # Suppress the development server warning
        # by not calling the parent's on_bind method that prints it
        self._suppress_warning = True
        return super().run(**options)

    def on_bind(self, server_port):
        """Override to suppress the warning message."""
        # Call parent but intercept the warning
        super().on_bind(server_port)

    def inner_run(self, *args, **options):
        """Override inner_run to suppress the warning."""
        # Store original write method
        original_write = self.stdout.write

        def filtered_write(msg, style_func=None, ending=None):
            """Filter out the development server warning."""
            if msg and "WARNING:" in msg and "development server" in msg:
                return  # Skip the warning
            if msg and "For more information on production servers" in msg:
                return  # Skip the link
            if style_func:
                if ending is not None:
                    original_write(msg, style_func=style_func, ending=ending)
                else:
                    original_write(msg, style_func=style_func)
            else:
                if ending is not None:
                    original_write(msg, ending=ending)
                else:
                    original_write(msg)

        # Replace write method temporarily
        self.stdout.write = filtered_write

        try:
            return super().inner_run(*args, **options)
        finally:
            # Restore original write method
            self.stdout.write = original_write

