import json
from argparse import ArgumentParser

from caelestia.command import BaseCommand, register
from caelestia.utils.logging import log_exception, log_message
from caelestia.utils.scheme import (
    Scheme,
    get_scheme,
    get_scheme_flavours,
    get_scheme_modes,
    get_scheme_names,
    scheme_variants,
)
from caelestia.utils.theme import apply_colours


def _configure(sub: ArgumentParser) -> None:
    """
    scheme {get|set|list}
    """
    sub.description = "Manage Caelestia color schemes."
    actions = sub.add_subparsers(dest="action", required=True)

    # scheme get [--json]
    get_p = actions.add_parser("get", help="Show the current scheme")
    get_p.add_argument("--json", action="store_true", help="Output as JSON")

    # scheme set (--name NAME | --random) [--flavour FLAV] [--mode auto|light|dark]
    set_p = actions.add_parser("set", help="Set the active scheme")
    grp = set_p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--name", help="Scheme name to apply")
    grp.add_argument("--random", action="store_true", help="Pick a random scheme")
    set_p.add_argument("--flavour", help="Flavour/variant (if the scheme has variants)")
    set_p.add_argument("--mode", choices=["auto", "light", "dark"], help="Preferred mode override")

    # scheme list [--names] [--flavours NAME]
    list_p = actions.add_parser("list", help="List available schemes")
    out_grp = list_p.add_mutually_exclusive_group()
    out_grp.add_argument("--names", action="store_true", help="List scheme names only")
    out_grp.add_argument("--flavours", metavar="NAME", help="List flavours for a specific scheme")


@register(
    "scheme",
    help="Get/set/list color schemes",
    configure_parser=_configure,
)
class SchemeCommand(BaseCommand):
    def run(self) -> None:
        action = self.args.action
        match action:
            case "get":
                self._do_get()
            case "set":
                self._do_set()
            case "list":
                self._do_list()
            case _:
                log_exception(f"Unknown scheme action: {action}")

    def _do_set(self) -> None:
        if self.args.name and self.args.name not in get_scheme_names():
            log_message(f'Invalid scheme name: "{self.args.name}". Valid: {get_scheme_names()}')
            return

        scheme = get_scheme()

        if self.args.notify:
            scheme.notify = True

        if self.args.random:
            scheme.set_random()
            apply_colours(scheme.colours, scheme.mode)
        elif self.args.name or self.args.flavour or self.args.mode or self.args.variant:
            if self.args.name:
                scheme.name = self.args.name
            if self.args.flavour:
                scheme.flavour = self.args.flavour
            if self.args.mode:
                scheme.mode = self.args.mode
            if self.args.variant:
                scheme.variant = self.args.variant
            apply_colours(scheme.colours, scheme.mode)
        else:
            print("No args given. Use --name, --flavour, --mode, --variant or --random to set a scheme")

    def _do_get(self) -> None:
        scheme = get_scheme()

        if self.args.json:
            print(json.dumps(scheme, ensure_ascii=False, indent=2))
            return

        name = getattr(scheme, "name", scheme.name)
        flavour = getattr(scheme, "flavour", scheme.flavour)
        mode = getattr(scheme, "mode", scheme.mode)
        print(f"{name} ({flavour}) [{mode}]")

    def _do_list(self) -> None:
        multiple = [self.args.names, self.args.flavours, self.args.modes, self.args.variants].count(True) > 1

        if self.args.names or self.args.flavours or self.args.modes or self.args.variants:
            if self.args.names:
                if multiple:
                    print("Names:", *get_scheme_names())
                else:
                    print("\n".join(get_scheme_names()))
            if self.args.flavours:
                if multiple:
                    print("Flavours:", *get_scheme_flavours())
                else:
                    print("\n".join(get_scheme_flavours()))
            if self.args.modes:
                if multiple:
                    print("Modes:", *get_scheme_modes())
                else:
                    print("\n".join(get_scheme_modes()))
            if self.args.variants:
                if multiple:
                    print("Variants:", *scheme_variants)
                else:
                    print("\n".join(scheme_variants))
        else:
            current_scheme = get_scheme()
            schemes = {}
            for scheme in get_scheme_names():
                schemes[scheme] = {}
                for flavour in get_scheme_flavours(scheme):
                    s = Scheme(
                        {
                            "name": scheme,
                            "flavour": flavour,
                            "mode": current_scheme.mode,
                            "variant": current_scheme.variant,
                            "colours": current_scheme.colours,
                        }
                    )
                    modes = get_scheme_modes(scheme, flavour)
                    if s.mode not in modes:
                        s._mode = modes[0]
                    try:
                        if hasattr(s, "_update_colours"):
                            s._update_colours()
                        schemes[scheme][flavour] = s.colours
                    except ValueError:
                        pass

            print(json.dumps(schemes))
