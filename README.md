# Roll For Shoes
A discord bot for running the Roll For Shoes roleplay system.

For reference, the complete (400ish word long) system rules are available here: https://gist.github.com/brunobord/8943645

To create a new character, use the `!newchar` command, e.g. `!newchar Krey`, to create a new character named "Krey" with 0 xp and the "do anything 1" ability.
This command automatically sets the new character as your default character.

(To switch to another existing character, use the `!usechar` command with the name of that character.)

Once you have a character, you can use the `!roll` command to initiate a skill check.
By default with no arguments `!roll` will use your current character's "do anything" ability.
This can be changed by specifying a character name, a skill name, or both.
Additionally, a comment can be added with `#` that will be included in the roll output.

For example:

```
!roll                 # Use the current character's do anything skill.
!roll fist o pain     # Use the current character's "Fist O'Pain" skill.
!roll ferret.         # Use Ferret's do anything skill.
!roll ryu.reptilian   # Use Ryu's reptilian skill.
```

(Note that names are matched on globs, so capitalization and punctuation do not matter.)

After issuing the `!roll` command, Roll For Shoes *does not make the roll immediately*, but rather defers it until it's resolved with either `!vs` or `!dc`.
In order to allow these later commands to refer to a specific roll, the bot instead reacts with a letter emoji to act as a token.
This token can be used later to refer to the roll, and is automatically removed once the `!roll` is resolved or expires.

Once any player has made a `!roll`, another player can oppose the roll with one of _their_ character's skills via the `!vs` command.
The semantics for this command are identical to those for `!roll`, except that they may optionally include a roll token as a single capital letter as the first argument.

The `!dc` command can also be used to oppose a roll with a value not associated with a character's skill check.
This command accepts a token similarily to `!vs`, but implements a more general dice expression parser capable of interpreting die expressions like `2d6 + 4`.

If no token is included, the command will respond to the most recent roll _in the same channel_.
With a token, the command will respond to that specific roll, even if it is in a _different_ channel.

```
[Player channel]
<Krey> !roll # Attack Ryu!
<bot reacts with "N">

<GM> !vs ryu.reptilian # Dodge

<bot> Krey wins!
        Attack Ryu! (krey.do-anything): 1d6 = [6] = 6 (!)
        Dodge (ryu.reptilian): 2d6 = [2 3] = 5 (+1, 1/2)

<Ferret> !roll boots of kicking # Kick down the door!
<bot reacts with "X">

[GM-only channel]
<GM> !dc X 2d6 # It's a really tough door.

[both channels simultaneously]
<bot> Ferret fails!
        Kick down the door! (ferret.boots-of-kicking): 2d6 = [3 2] = 5 (+1, 7/2)
        It's a really tough door. DC 2d6 = 9
```

When skill rolls are resolved, the bot automatically gives the loser 1 XP and updates both skills with the amount of XP needed to level up.
Automatic level-ups from rolling all 6's are denoted with a `(!)`.

You can also check pending level-ups from the character sheet with `!char`.
Any pending level-ups from all 6's are shown with a `(!)`, and any skill eligible to be leveled by spending XP is shown with the XP cost in parenthesis.

```
!char

Krey
  XP: 2
Skills
  do anything 1 (!)
  ┣ Fist O'Pain 2
  ┃ ┗ Burning Fist O'Pain 3
  ┣ Heretic 2
  ┗ Teeth of Biting 2
```


To level a skill, use the `!levelup` command.
Sematics for specifying the parent skill are the same as for other commands; the new skill after the `>` is then added under it at one level higher.
Experience points are automatically deducted as required for the level-up.

```
!levelup > dodge                     # level up "do anything 1" to "dodge 2"
!levelup ryu.reptilian > slithering  # level up Ryu's "reptilian 2" skill to "slithering 3"
```

For fixing mistakes there is an `!edit` command with a number of subcommands.
For more information type `!help edit`.


TODO:

- role-based command restrictions
- commands for migrating/synchronizing characters between servers
- unit tests
- web UI