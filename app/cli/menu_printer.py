# app/cli/menu_printer.py
from typing import Iterable, Optional, Any
import difflib
from decimal import Decimal
from rich.console import Console
from rich.table import Table

from app.cli.input_collector import get_string, get_int, get_float
from app.service.exceptions import ValidationError, NotFoundError
from app.cli.constants import APP_NAME

class MenuPrinter:
    """
    Helper to print numbered menus to the console using rich.
    Accepts service instances so the caller (main.py) can pass dependencies.
    """
    def __init__(
        self,
        login_service: Any,
        user_service: Any,
        portfolio_service: Any,
        security_service: Any,
        console: Optional[Console] = None,
    ) -> None:
        # store services provided by the application bootstrap (main.py)
        self.login_service = login_service
        self.user_service = user_service
        self.portfolio_service = portfolio_service
        self.security_service = security_service
        self.console = console or Console()

    def print_menu(self, options: Iterable[str], title: str = APP_NAME) -> None:
        """
        Print a numbered menu.

        Args:
            title: header/title for the menu
            options: iterable of menu option strings (will be numbered starting at 1)
        """
        table = Table(title=title, show_header=False, box=None)
        table.add_column("", no_wrap=True)
        table.add_column("", no_wrap=False)
        for idx, opt in enumerate(options, start=1):
            table.add_row(f"{idx}", opt)
        self.console.print(table)

    def prompt_choice(self, max_choice: int, prompt_text: str = "Select option") -> int:
        """
        Prompt for a numeric choice between 1 and max_choice (inclusive).
        Returns the chosen integer. Caller should handle exceptions/looping as needed.
        """
        while True:
            try:
                choice_raw = self.console.input(f"[bold]{prompt_text}[/bold] > ")
                if choice_raw is None or choice_raw.strip() == "":
                    self.console.print("[red]Please enter a choice.[/red]")
                    continue
                choice = int(choice_raw)
                if 1 <= choice <= max_choice:
                    return choice
                self.console.print(f"[red]Please enter a number between 1 and {max_choice}.[/red]")
            except ValueError:
                self.console.print("[red]Invalid input. Enter a number.[/red]")
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[red]Input cancelled.[/red]")
                return 0

    # --- New methods added below ---
    def run(self) -> None:
        """
        Start the top-level application loop (login menu -> main menu).
        Minimal implementation: supports Login and Exit. After successful login,
        shows a placeholder main menu with Logout implemented.
        """
        while True:
            self.print_menu(["Login", "Exit"], "Login Menu")
            choice = self.prompt_choice(2, "Choose an option")
            if choice == 0:
                # cancelled input; loop back to show menu again
                continue
            if choice == 2:
                self.console.print("[green]Goodbye.[/green]")
                break
            if choice == 1:
                username = get_string("Username")
                if username == "":
                    continue
                password = get_string("Password")
                if password == "":
                    continue
                auth_ok = False
                try:
                    if self.login_service:
                        auth_ok = self.login_service.authenticate(username, password)
                except Exception as e:
                    self.console.print(f"[red]Authentication error: {e}[/red]")
                    auth_ok = False
                if auth_ok:
                    self.console.print(f"[green]Welcome, {username}![/green]")
                    # enter main menu for the logged in user
                    self._main_menu(username)
                else:
                    self.console.print("[red]Invalid credentials. Try again.[/red]")

    def _main_menu(self, username: str) -> None:
        """Main menu loop with implemented menus."""
        while True:
            self.print_menu([
                    "Manage Users",
                    "Manage Portfolios",
                    "Marketplace",
                    "View Transactions",
                    "View Balance",
                    "Logout"
            ], "Main Menu")
            choice = self.prompt_choice(6, "Choose an option")
            if choice == 0:
                continue
            if choice == 6:
                try:
                    if self.login_service:
                        self.login_service.logout()
                except Exception:
                    pass
                self.console.print("[yellow]Logged out.[/yellow]")
                break
            if choice == 1:
                if username != "admin":
                    self.console.print("[red]Access denied. Only admin can manage users.[/red]")
                else:
                    self._manage_users_menu()
            elif choice == 2:
                self._manage_portfolios_menu(username)
            elif choice == 3:
                self._marketplace_menu(username)
            elif choice == 4:
                self._view_transactions_menu(username)
            elif choice == 5:
                self._view_balance(username)
    def _view_balance(self, username: str) -> None:
        """Display the user's available cash balance."""
        try:
            user = self.user_service.get_user(username)
            if not user:
                self.console.print(f"[red]User '{username}' not found.[/red]")
                return
            balance = getattr(user, "balance", None)
            if balance is None:
                self.console.print(f"[red]Balance not available for user '{username}'.[/red]")
                return
            self.console.print(f"[bold green]Available Balance: ${balance:.2f}[/bold green]")
        except Exception as e:
            self.console.print(f"[red]Error retrieving balance: {e}[/red]")

    def _manage_users_menu(self) -> None:
        """Manage Users submenu for admin."""
        while True:
            self.print_menu(["View Users", "Add User", "Delete User", "Deposit Money", "Back to Main Menu"], "Manage Users")
            choice = self.prompt_choice(5, "Choose an option")
            if choice == 0:
                continue
            if choice == 5:
                break  # back to main menu
            if choice == 1:
                self._view_users()
            elif choice == 2:
                self._add_user()
            elif choice == 3:
                self._delete_user()
            elif choice == 4:
                self._deposit_money()

    def _view_users(self) -> None:
        """Display all users in a table."""
        try:
            users = self.user_service.list_users()
            if not users:
                self.console.print("[yellow]No users found.[/yellow]")
                return
            table = Table(title="Users")
            table.add_column("First Name", style="cyan")
            table.add_column("Last Name", style="cyan")
            table.add_column("Username", style="cyan")
            table.add_column("Balance", style="green")
            for user in users:
                bal = getattr(user, 'balance', None)
                try:
                    bal_disp = Decimal(bal) if bal is not None else Decimal('0.00')
                except Exception:
                    bal_disp = bal
                table.add_row(
                    str(getattr(user, "first_name", "")),
                    str(getattr(user, "last_name", "")),
                    str(getattr(user, "username", "")),
                    f"${bal_disp:.2f}",
                )
            self.console.print(table)
        except Exception as e:
            self.console.print(f"[red]Error viewing users: {e}[/red]")

    def _add_user(self) -> None:
        """Prompt for user details and add a new user."""
        try:
            first_name = get_string("First name")
            if first_name == "":
                return
            last_name = get_string("Last name")
            if last_name == "":
                return
            username = get_string("Username")
            if username == "":
                return
            password = get_string("Password")
            if password == "":
                return
            balance = get_float("Initial balance", min_value=0.0)
            if balance < 0:
                return
            role = get_string("Role (admin/customer)") or "customer"
            # Add user via service
            new_user = self.user_service.create_user(first_name, last_name, username, password, balance, role)
            if new_user:
                self.console.print(f"[green]User {username} added successfully.[/green]")
            else:
                self.console.print("[red]Failed to add user.[/red]")
        except Exception as e:
            self.console.print(f"[red]Error adding user: {e}[/red]")

    def _delete_user(self) -> None:
        """Prompt for username and delete the user."""
        try:
            username = get_string("Username of the user to delete")
            if username == "":
                return
            # Check that the user exists before asking for confirmation
            try:
                _ = self.user_service.get_user(username)
            except NotFoundError:
                self.console.print(f"[red]User {username} not found.[/red]")
                return

            confirm = get_string(f"Confirm deletion of user '{username}'? (yes/no)")
            if confirm.strip().lower() == "yes":
                try:
                    self.user_service.delete_user(username)
                    self.console.print(f"[green]User {username} deleted successfully.[/green]")
                except ValidationError as ve:
                    self.console.print(f"[red]{ve}[/red]")
                except NotFoundError:
                    # Ideally shouldn't happen because we checked, but handle defensively
                    self.console.print(f"[red]User {username} not found.[/red]")
        except Exception as e:
            self.console.print(f"[red]Error deleting user: {e}[/red]")

    def _deposit_money(self) -> None:
        """Prompt for username and amount, then deposit money to the user's account."""
        try:
            username = get_string("Username to deposit money to")
            if username == "":
                return
            amount = get_float("Amount to deposit", min_value=0.01)
            if amount is None:
                return
            self.user_service.deposit(username, amount)
            self.console.print(f"[green]Deposited ${amount:.2f} to {username}'s account.[/green]")
        except Exception as e:
            self.console.print(f"[red]Error depositing money: {e}[/red]")

    def _manage_portfolios_menu(self, username: str) -> None:
        """Manage Portfolios submenu."""
        while True:
            self.print_menu([
                "View Portfolios",
                "Create Portfolio",
                "Delete Portfolio",
                "Harvest Investment",
                "Back to Main Menu"
            ], "Manage Portfolios")
            choice = self.prompt_choice(5, "Choose an option")
            if choice == 0:
                continue
            if choice == 5:
                break  # back to main menu
            if choice == 1:
                self._view_portfolios(username)
            elif choice == 2:
                self._create_portfolio(username)
            elif choice == 3:
                self._delete_portfolio(username)
            elif choice == 4:
                self._harvest_investment(username)
    def _harvest_investment(self, username: str) -> None:
        """Prompt for portfolio ID, ticker, quantity, and sale price, then harvest investment."""
        try:
            portfolio_id = get_int("Portfolio ID to harvest from", min_value=1)
            if portfolio_id is None:
                return
            ticker = get_string("Ticker symbol to harvest")
            if not ticker:
                return
            quantity = get_int("Quantity to harvest", min_value=1)
            if quantity is None:
                return
            # Get current market price from security_service
            security = self.security_service.get_security(ticker)
            if not security:
                self.console.print(f"[red]Security '{ticker}' not found.[/red]")
                return
            sale_price = security.price
            proceeds = self.portfolio_service.harvest_investment(
                username, portfolio_id, ticker, quantity, sale_price
            )
            self.console.print(f"[green]Harvested {quantity} shares of {ticker} from portfolio {portfolio_id} at market price ${sale_price:.2f}/share. Proceeds: ${proceeds:.2f}[/green]")
        except ValidationError as ve:
            self.console.print(f"[red]Harvest failed: {ve}[/red]")
        except NotFoundError as ne:
            self.console.print(f"[red]Harvest error: {ne}[/red]")
        except Exception as e:
            self.console.print(f"[red]Unexpected error during harvest: {e}[/red]")

    def _view_portfolios(self, username: str) -> None:
        """Display all portfolios of the user in a table."""
        try:
            portfolios = self.portfolio_service.get_portfolios_by_username(username)
            if not portfolios:
                self.console.print("[yellow]No portfolios found.[/yellow]")
                return
            table = Table(title="Portfolios")
            table.add_column("Portfolio ID", style="magenta")
            table.add_column("Portfolio Name", style="cyan")
            table.add_column("Assets (Amount Invested)", style="green")
            for portfolio in portfolios:
                # Calculate amount invested for each asset using Security price
                if portfolio.holdings:
                    parts = []
                    for inv in portfolio.holdings:
                        try:
                            from decimal import Decimal
                            sec_price = Decimal(self.security_service.get_security(inv.ticker).price)
                            amount_invested = Decimal(inv.quantity) * sec_price
                            parts.append(f"{inv.ticker} (${amount_invested:.2f}, {inv.quantity:.4f} shares)")
                        except Exception:
                            parts.append(f"{inv.ticker} (error computing value)")
                    assets = ", ".join(parts)
                else:
                    assets = "No assets"
                table.add_row(str(portfolio.id), str(portfolio.name), str(assets))
            self.console.print(table)
        except Exception as e:
            self.console.print(f"[red]Error viewing portfolios: {e}[/red]")

    def _create_portfolio(self, username: str) -> None:
        """Prompt for portfolio details and create a new portfolio."""
        try:
            name = get_string("Portfolio name")
            if name == "":
                return
            description = get_string("Portfolio description")
            if description == "":
                return
            # Create portfolio via service
            new_portfolio = self.portfolio_service.create_portfolio(username, name, description)
            if new_portfolio:
                self.console.print(f"[green]Portfolio '{name}' (ID: {new_portfolio.id}) created successfully.[/green]")
            else:
                self.console.print("[red]Failed to create portfolio.[/red]")
        except Exception as e:
            self.console.print(f"[red]Error creating portfolio: {e}[/red]")

    def _delete_portfolio(self, username: str) -> None:
        """Prompt for portfolio ID and delete the portfolio."""
        try:
            portfolio_id = get_int("Portfolio ID to delete", min_value=1)
            if portfolio_id is None:
                return
            confirm = get_string(f"Confirm deletion of portfolio ID '{portfolio_id}'? (yes/no)")
            if confirm.strip().lower() == "yes":
                self.portfolio_service.delete_portfolio(username, portfolio_id)
                self.console.print(f"[green]Portfolio ID '{portfolio_id}' deleted successfully.[/green]")
            else:
                self.console.print("[yellow]Deletion cancelled.[/yellow]")
        except ValidationError as ve:
            self.console.print(f"[red]Failed to delete portfolio: {ve}[/red]")
        except NotFoundError as ne:
            self.console.print(f"[red]Error: {ne}[/red]")
        except Exception as e:
            self.console.print(f"[red]Unexpected error deleting portfolio: {e}[/red]")

    def _marketplace_menu(self, username: str) -> None:
        """Marketplace menu for buying and selling securities."""
        while True:
            self.print_menu(["View Securities", "Buy Security", "Sell Security", "Back to Main Menu"], "Marketplace")
            choice = self.prompt_choice(4, "Choose an option")
            if choice == 0:
                continue
            if choice == 4:
                break  # back to main menu
            if choice == 1:
                self._view_securities()
            elif choice == 2:
                self._buy_security(username)
            elif choice == 3:
                self._sell_security(username)

    def _view_transactions_menu(self, username: str) -> None:
        """Menu to view transactions by user, portfolio, or security."""
        while True:
            self.print_menu([
                "By User",
                "By Portfolio",
                "By Security",
                "Back to Main Menu"
            ], "View Transactions")
            choice = self.prompt_choice(4, "Choose an option")
            if choice == 0:
                continue
            if choice == 4:
                break
            try:
                if choice == 1:
                    # By user
                    user = get_string("Username to view transactions for")
                    if not user:
                        continue
                    # resolve user id
                    u = self.user_service.get_user(user)
                    txs = self.security_service.get_transactions_by_user(u.id, username)
                    self._print_transactions(txs)
                elif choice == 2:
                    pid = get_int("Portfolio ID to view transactions for", min_value=1)
                    if pid is None:
                        continue
                    txs = self.security_service.get_transactions_by_portfolio(pid, username)
                    self._print_transactions(txs)
                elif choice == 3:
                    ticker = get_string("Security ticker to view transactions for")
                    if not ticker:
                        continue
                    txs = self.security_service.get_transactions_by_security(ticker, username)
                    self._print_transactions(txs)
            except NotFoundError as ne:
                self.console.print(f"[red]{ne}[/red]")
            except PermissionError as pe:
                self.console.print(f"[red]Permission denied: {pe}[/red]")
            except Exception as e:
                self.console.print(f"[red]Error retrieving transactions: {e}[/red]")

    def _print_transactions(self, transactions: list) -> None:
        """Render a list of Transaction ORM objects in a table."""
        if not transactions:
            self.console.print("[yellow]No transactions found.[/yellow]")
            return
        table = Table(title="Transactions")
        table.add_column("ID", style="magenta")
        table.add_column("Timestamp", style="cyan")
        table.add_column("User", style="cyan")
        table.add_column("Portfolio ID", style="green")
        table.add_column("Security", style="green")
        table.add_column("Action", style="yellow")
        table.add_column("Quantity", style="green")
        table.add_column("Price", style="green")
        for tx in transactions:
            user_name = getattr(tx, "user", None)
            # user may be a relationship object or None; attempt to show username
            uname = getattr(user_name, "username", str(getattr(tx, "user_id", "")))
            try:
                from decimal import Decimal
                price_disp = Decimal(getattr(tx, 'price', Decimal('0.00')))
            except Exception:
                price_disp = getattr(tx, 'price', '')
            table.add_row(
                str(getattr(tx, "id", "")),
                str(getattr(tx, "timestamp", "")),
                str(uname),
                str(getattr(tx, "portfolio_id", "")),
                str(getattr(tx, "security_id", "")),
                str(getattr(tx, "action", "")),
                str(getattr(tx, "quantity", "")),
                f"${price_disp:.2f}",
            )
        self.console.print(table)

    def _view_securities(self) -> None:
        """Display all available securities in a table."""
        try:
            securities = self.security_service.list_securities()
            if not securities:
                self.console.print("[yellow]No securities found.[/yellow]")
                return
            table = Table(title="Securities")
            table.add_column("Symbol", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Price", style="green")
            for security in securities:
                table.add_row(
                    str(getattr(security, "ticker", "")),
                    str(getattr(security, "name", "")),
                    f"${Decimal(getattr(security, 'price', Decimal('0.00'))):.2f}",
                )
            self.console.print(table)
        except Exception as e:
            self.console.print(f"[red]Error viewing securities: {e}[/red]")

    def _buy_security(self, username: str) -> None:
        """Prompt for security symbol, amount, and portfolio ID, then buy the security."""
        try:
            # Prompt for symbol and validate; allow retries and suggestions
            while True:
                symbol = get_string("Security symbol to buy (or type 'list' to show available)")
                if symbol == "":
                    return
                if symbol.strip().lower() == "list":
                    self._view_securities()
                    continue
                # quick existence check
                try:
                    _ = self.security_service.get_security(symbol)
                    break
                except NotFoundError:
                    # suggest close matches
                    try:
                        all_secs = self.security_service.list_securities()
                        tickers = [s.ticker for s in all_secs]
                    except Exception:
                        tickers = []
                    matches = difflib.get_close_matches(symbol.upper(), tickers, n=3, cutoff=0.6)
                    if matches:
                        self.console.print(f"[yellow]Ticker '{symbol}' not found. Did you mean: {', '.join(matches)} ?[/yellow]")
                    else:
                        self.console.print(f"[red]Ticker '{symbol}' not found.[/red]")
                    retry = get_string("Retry ticker? (yes/no)")
                    if retry.strip().lower() != "yes":
                        return
            amount = get_float("Amount to invest", min_value=0.01)
            if amount is None:
                return

            # Portfolio selection/creation flow
            try:
                portfolios = self.portfolio_service.get_portfolios_by_username(username)
            except NotFoundError:
                self.console.print(f"[red]User '{username}' not found.[/red]")
                return

            portfolio_id = None
            if not portfolios:
                # No portfolios — offer to create one
                create = get_string("You don't have any portfolios. Create one now? (yes/no)")
                if create.strip().lower() != "yes":
                    self.console.print("[yellow]Buy cancelled — no portfolio selected.[/yellow]")
                    return
                name = get_string("Portfolio name")
                if name == "":
                    return
                description = get_string("Portfolio description")
                if description == "":
                    description = ""
                new_port = self.portfolio_service.create_portfolio(username, name, description)
                portfolio_id = new_port.id
                self.console.print(f"[green]Created portfolio '{name}' (ID: {portfolio_id}).[/green]")
            else:
                # Show brief list and allow selection or creation
                self.console.print("[bold]Your portfolios:[/bold]")
                for p in portfolios:
                    self.console.print(f"  {p.id}: {getattr(p, 'name', '')}")
                while True:
                    choice = get_string("Enter Portfolio ID to invest in or type 'new' to create a portfolio")
                    if not choice:
                        return
                    if choice.strip().lower() == "new":
                        name = get_string("Portfolio name")
                        if name == "":
                            return
                        description = get_string("Portfolio description")
                        if description == "":
                            description = ""
                        new_port = self.portfolio_service.create_portfolio(username, name, description)
                        portfolio_id = new_port.id
                        self.console.print(f"[green]Created portfolio '{name}' (ID: {portfolio_id}).[/green]")
                        break
                    try:
                        pid = int(choice)
                    except ValueError:
                        self.console.print("[red]Invalid input. Enter a numeric portfolio ID or 'new'.[/red]")
                        continue
                    if any(p.id == pid for p in portfolios):
                        portfolio_id = pid
                        break
                    else:
                        self.console.print("[red]You do not own that portfolio. Choose again.[/red]")

            # Execute buy via service
            self.security_service.buy_security(username, symbol, amount, portfolio_id)
            self.console.print(f"[green]Successfully bought ${amount:.2f} of {symbol} in portfolio {portfolio_id}.[/green]")
        except PermissionError as pe:
            self.console.print(f"[red]Permission denied: {pe}[/red]")
        except ValueError as ve:
            self.console.print(f"[red]Failed to buy {symbol}: {ve}[/red]")
        except Exception as e:
            self.console.print(f"[red]Unexpected error buying security: {e}[/red]")
            self.console.print(f"[yellow]Details: {e.args}[/yellow]")

    def _sell_security(self, username: str) -> None:
        """Prompt for security symbol, amount, and portfolio ID, then sell the security."""
        try:
            symbol = get_string("Security symbol to sell")
            if symbol == "":
                return
            amount = get_float("Amount to sell", min_value=0.01)
            if amount is None:
                return

            # Prompt for portfolio ID
            portfolio_id = get_int("Portfolio ID to sell from", min_value=1)
            if portfolio_id is None:
                return

            # Execute sell via service
            self.security_service.sell_security(username, symbol, amount, portfolio_id)
            self.console.print(f"[green]Successfully sold ${amount:.2f} of {symbol} from portfolio {portfolio_id}.[/green]")
        except PermissionError as pe:
            self.console.print(f"[red]Permission denied: {pe}[/red]")
        except ValueError as ve:
            self.console.print(f"[red]Failed to sell {symbol}: {ve}[/red]")
        except Exception as e:
            self.console.print(f"[red]Unexpected error selling security: {e}[/red]")
            self.console.print(f"[yellow]Details: {e.args}[/yellow]")