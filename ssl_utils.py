"""
nrcan_ssl
---------
Manages NRCan network ca bundle.

Appends NRCan ca and temporarily rests ca bundles set for :

- REQUESTS_CA_BUNDLE
- CURL_CA_BUNDLE
- AWS_CA_BUNDLE
- SSL_CERT_FILE

If the env vars are not set, it sets them
to temporary version of certifi/cacert.pem with NRCan ca appended.
Defaults to NRCan-Root-2019-B64.cer in same directory as ssl_utils.py

Examples
--------
As decorator
------------
    from nrcan_ssl.ssl_utils import nrcan_ca_patch
    def <function_that_needs_patch>():
        # ...

As module
------
    from nrcan_ssl.ssl_utils import SSLUtils

    ssl_utils = SSLUtils()
    ssl_utils.set_nrcan_ssl()
    # <code that requires ssl set>
    ssl_utils.unset_nrcan_ssl()

As CLI - Not recommended.  Only creates and deletes temp ca bundles.
------
    WARNING    Take note of the original env var settings.
    WARNING    You will have to temporarily set your env vars manually
    WARNING    You will have to reset your env vars manually
    WARNING    You will have to delete your temp_ca_bundels directory manually

    python <path-to>/ssl_utils.py --set-nrcan
    # Take note of orgininal settings,
    # Temporarilly set env vars manually
    # Reset env vars to original settings manually
    # Delete temp ca bundle directory manually

    python <path-to>/ssl_utils.py --unset-nrcan
    # Only deletes temp ca bundle directory

"""

# Python standard library
import argparse
from datetime import datetime
from functools import wraps
import os
import pathlib
import shutil
import sys

# Python custom packages
import certifi


# Decorators
def nrcan_ca_patch(f):
    @wraps(f)
    def ca_wrapper(*args, **kwargs):
        """Temporarily sets *_CA_BUNDLE to NRCAN ca"""
        ssl_utils = SSLUtils()
        # Set env var to nrcan_ca
        ssl_utils.set_nrcan_ssl()
        # Execute decorated function
        result = f(*args, **kwargs)
        # Set env var back to original value
        ssl_utils.unset_nrcan_ssl()
        return result

    return ca_wrapper


# Function
def cli(set: bool = True, unset: bool = False, path: str = None):
    """Manages CLI version of ssl util"""

    print("WARNING:   This is not recommended, use with caution", file=sys.stdout)

    if isinstance(path, str):
        # Convert path to pathlib
        path = pathlib.Path(path)

    if set:
        print("WARNING    Take note of the original env var settings.", file=sys.stdout)
        print(
            "WARNING    You will have to temporarilly set your env vars manually",
            file=sys.stdout,
        )
        print(
            "WARNING    You will have to reset your env vars manually", file=sys.stdout
        )
        print(
            "WARNING    You will have to delete your temp_ca_bundels directory manually",
            file=sys.stdout,
        )
        ssl_utils = SSLUtils(nrcan_ca_path=path, keep_temp=True, verbose=True)
        ssl_utils.set_nrcan_ssl()

    if unset:
        print(
            "WARNING    This only deletes your temp_ca_bundels directory",
            file=sys.stdout,
        )
        print(
            "WARNING    You will have to reset your env vars manually", file=sys.stdout
        )
        ssl_utils = SSLUtils(nrcan_ca_path=path, keep_temp=False, verbose=True)
        ssl_utils.unset_nrcan_ssl()
    return


def _handle_args():
    parser = argparse.ArgumentParser(
        prog="NRCan ssl managment", description="Appends NRCan ca to ca env vars"
    )
    parser.add_argument(
        "-s", "--set_nrcan", help="Set the nrcan ca bundles", action="store_true"
    )
    parser.add_argument(
        "-u", "--unset_nrcan", help="Set the nrcan ca bundles", action="store_true"
    )
    parser.add_argument("-p", "--path", help="Path to NRCan ca bundle")

    args = parser.parse_args()

    cli(set=args.set_nrcan, unset=args.unset_nrcan, path=args.path)
    return


# Classes
class SSLUtils:
    def __init__(
        self,
        env_vars: list = None,
        nrcan_ca_path: str = None,
        keep_temp: bool = False,
        verbose: bool = False,
    ):
        """Initializes the instance of certificat management.

        Args:
            env_vars (list, optional): _description_. Defaults to None.
            nrcan_ca_path (str, optional): _description_. Defaults to None.
            keep_temp (bool, optional): _description_. Defaults to False.
            verbose (bool, optional): _description_. Defaults to False.
        """

        self.default_nrcan_ca = (
            pathlib.Path(__file__).parent / "NRCAN-Root-2019-B64.cer"
        )
        self.default_env_vars = [
            "REQUESTS_CA_BUNDLE",
            "CURL_CA_BUNDLE",
            "AWS_CA_BUNDLE",
            "SSL_CERT_FILE",
        ]
        self._keep_temp = keep_temp

        if (
            env_vars
            and isinstance(env_vars, list)
            and env_vars in self.default_env_vars
        ):
            self.env_vars = env_vars
        else:
            self.env_vars = self.default_env_vars
        if nrcan_ca_path:
            temp = pathlib.Path(nrcan_ca_path)
            if temp.is_file():
                self.nrcan_ca = temp
            else:
                self.nrcan_ca = self.default_nrcan_ca
        else:
            self.nrcan_ca = self.default_nrcan_ca

        self.certifi = pathlib.Path(certifi.where())
        self.existing_values = self.get_existing_values()
        self.verbose = verbose

        # Write temp ca_bundle with NRCan SSL to cwd/nrcan_ssl
        root_ca_dir = datetime.now().isoformat(timespec="hours")
        self.temp_root_ca_dir = pathlib.Path.cwd() / f"nrcan-ssl-{root_ca_dir}"
        self.temp_ca_dir = self.temp_root_ca_dir / "temp_ca_bundles"
        if not self.temp_ca_dir.is_dir():
            self.temp_ca_dir.mkdir(parents=True, exist_ok=True)

        self.temp_values = {}

        if self.verbose:
            print(
                f"INFO:    SSLUtils existing_values {self.existing_values}",
                file=sys.stdout,
            )

    def __del__(self):
        self.unset_nrcan_ssl()

    def get_existing_values(self):
        existing = {}

        # Get existing value for env var
        for env_var in self.env_vars:
            if env_var in os.environ:
                existing[env_var] = os.environ[env_var]
            else:
                existing[env_var] = None

        return existing

    def set_nrcan_ssl(self):
        """
        Temporarily sets 'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE',
        'AWS_CA_BUNDLE', 'SSL_CERT_FILE'
        to NRCAN ca.


        Uses existing_values to create temp versions of
        each full ca bundle with nrcan cert appended to it
        Temporarily sets that env var to nrcan appended version of ca bundle.
        If no env vars are set, then each is temporarily assigned a

        Required
        --------
            - before calls to Datacube AWS based API
            - others

        Example
        ---------
            # Instantinate SSL_Utils class
            ssl_utils = SSLUtils()

            # SET CA_BUNDLE env vars
            ssl_utils.set_nrcan_ssl()

            # Run code that needs it
            # ...

            # Unset env vars
            ssl_utils.unset_nrcan_ssl()
        """

        if sys.platform == "win32":
            # Copy any existing ca_bundels locally
            # Append the NRCAN ca_bundle
            # Set this as new ca_bundle
            if not self.temp_ca_dir.is_dir():
                self.temp_ca_dir.mkdir(exist_ok=True, parents=True)

            # Create a local temp copy of certifi cacert.pem
            self.temp_ca_bundle = self.temp_ca_dir / self.certifi.name
            shutil.copy(str(self.certifi.absolute()), str(self.temp_ca_bundle))

            # Append NRCan ca to temp certifi cacert.pem ca bundle
            self.append_nrcan_ca(self.temp_ca_bundle)

            for k, v in self.existing_values.items():
                if v:
                    temp_cer = self.temp_ca_dir / f"{k}.cer"
                    # Create copy in temp ca bundle directory
                    shutil.copy(v, str(temp_cer.absolute()))
                    # Append nrcan ca to temp ca bundle
                    self.append_nrcan_ca(temp_cer)
                    self.temp_values.update({k: str(temp_cer.absolute())})
                else:
                    # Use temp ca bundle for each
                    self.temp_values.update({k: str(self.temp_ca_bundle.absolute())})

            if self.verbose:
                print("INFO:    Temporarily Setting")
            for env_var, temp_ca in self.temp_values.items():
                os.environ[env_var] = temp_ca
                if self.verbose:
                    print(f"{env_var}={temp_ca}", file=sys.stdout)

    def append_nrcan_ca(self, ca_bundle: pathlib.Path):
        # Append nrcan ca to existing ca_bundle file
        with ca_bundle.open("a") as fp:
            with self.nrcan_ca.open("r") as np:
                lines = np.readlines()
            fp.writelines(lines)
        return

    def unset_nrcan_ssl(self):
        """Set env var back to original value.

        Example
        ------------
        See set_nrcan_ssl()
        """
        if sys.platform == "win32":
            if self.verbose:
                print("INFO:    Reseting to original values:")
            for env_var, existing_ca in self.existing_values.items():
                if existing_ca:
                    # Reset to original value
                    os.environ[env_var] = existing_ca
                else:
                    # Delete env var if it did not exist before and has not already been deleted
                    if env_var in os.environ.keys():
                        del os.environ[env_var]
                if self.verbose:
                    print(f"{env_var}={existing_ca}", file=sys.stdout)

            if self.verbose:
                print(
                    f"INFO:    Reset existing_values {self.existing_values}",
                    file=sys.stdout,
                )

            # Removing all temp values
            if not self._keep_temp:
                if self.temp_root_ca_dir.is_dir():
                    shutil.rmtree(
                        str(self.temp_root_ca_dir.absolute()), ignore_errors=True
                    )
                if self.verbose:
                    print(
                        "INFO:    "
                        "Deleted temp ca bundle dir"
                        f" {self.temp_root_ca_dir.absolute()}",
                        file=sys.stdout,
                    )


if __name__ == "__main__":
    _handle_args()
