from typing import Tuple, Optional, Dict, Any

import click
from tabulate import tabulate

from elisctl.arguments import id_argument
from elisctl.lib import QUEUES, GROUPS, USERS
from elisctl.lib.api_client import ELISClient
from elisctl.user import create
from elisctl.user.options import queue_option, group_option, locale_option, password_option


@click.group("user")
def cli() -> None:
    pass


cli.add_command(create.create_command)


@cli.command(name="list", help="List all users.")
@click.pass_context
def list_command(ctx: click.Context,):
    with ELISClient(context=ctx.obj) as elis:
        users_list = elis.get_users((QUEUES, GROUPS), is_active=True)

    table = [
        [
            user["id"],
            user["username"],
            ", ".join(str(g["name"]) for g in user[str(GROUPS)]),
            ", ".join(str(q["id"]) for q in user[str(QUEUES)]),
        ]
        for user in users_list
    ]

    click.echo(tabulate(table, headers=["id", "username", "groups", "queues"]))


@cli.command(name="change", help="Change a user.")
@id_argument
@queue_option
@group_option(default=None, show_default=False)
@locale_option(default=None, show_default=False)
@password_option(help=None)
@click.pass_context
def change_command(
    ctx: click.Context,
    id_: int,
    queue_id: Tuple[int],
    group: Optional[str],
    locale: Optional[str],
    password: Optional[str],
) -> None:
    if not any([queue_id, group, locale, password]):
        return

    data: Dict[str, Any] = {}
    if password is not None:
        data["password"] = password

    with ELISClient(context=ctx.obj) as elis:
        if queue_id:
            data[str(QUEUES)] = [elis.get_queue(queue)["url"] for queue in queue_id]
        if group is not None:
            data[str(GROUPS)] = [g["url"] for g in elis.get_groups(group_name=group)]
        if locale is not None:
            ui_settings = elis.get_user(id_)["ui_settings"]
            data["ui_settings"] = {**ui_settings, "locale": locale}

        elis.patch(f"{USERS}/{id_}", data)


@cli.command(name="delete", help="Delete a user.")
@click.argument("id_", metavar="ID", type=str)
@click.confirmation_option()
@click.pass_context
def delete_command(ctx: click.Context, id_: str) -> None:
    with ELISClient(context=ctx.obj) as elis:
        elis.patch(f"{USERS}/{id_}", {"is_active": False})
