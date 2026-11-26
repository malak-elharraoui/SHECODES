# opsh — Mini-Shell en Python

**Projet semestriel — Systèmes d'Exploitation**
École Supérieure d'Informatique et du Numérique (UIR / ESIN)

**Projet 2 :** mini-shell fonctionnel en Python (`opsh`)

---

## Table des matières

1. [Description](#1-description)
2. [Jalons du projet](#2-jalons-du-projet)
3. [Prérequis](#3-prérequis)
4. [Installation](#4-installation)
5. [Exécution](#5-exécution)
6. [Commandes disponibles](#6-commandes-disponibles)
7. [Exemples d'utilisation](#7-exemples-dutilisation)
8. [Complétion avec la touche Tab](#8-complétion-avec-la-touche-tab)
9. [Codes de retour](#9-codes-de-retour)
10. [Architecture du code](#10-architecture-du-code)
11. [Limites connues](#11-limites-connues)
12. [Contenu du dépôt](#12-contenu-du-dépôt)

---

## 1. Description

`opsh` est un interpréteur de commandes écrit en Python. Il lit une commande, la découpe, puis soit l'exécute lui-même (**builtin**), soit crée un processus fils avec `os.fork()` et lance le programme avec `os.execvp()`.

Il reproduit les mécanismes réels de Bash (redirections, pipes, signaux, variables, scripts, job control) avec :

- des **commandes renommées** (`go`, `path`, `say`, `list`, `show`...) ;
- l'opérateur de pipe **`->`** à la place de `|` ;
- le builtin **`osinfo`**, qui affiche `Systèmes d'Exploitation -- UIR/ESIN`.

Le shell n'utilise que la bibliothèque standard de Python (`os`, `signal`, `shlex`, `re`, `readline`).

## 2. Jalons du projet

| Jalon | Contenu |
|:---:|---|
| 1 | Boucle REPL : prompt `opsh>`, lecture, découpage par `->`, exécution via `os.fork()` |
| 2 | Builtins et alias de la table, redirections `>` `>>` `<` |
| 3 | Pipes `->`, arrière-plan `&`, signaux `SIGINT` / `SIGCHLD` |
| 4 | Variables et expansion : `$VAR`, `${VAR}`, `export`, `$?`, `$!` (en plus : `$$` et `$((...))`) |
| 5 | Substitution `$(...)` et backticks, `.opshrc`, historique et complétion |
| 6 | Mode script `opsh script.opsh` (`if` / `for` / `while`) |
| 6 *(option)* | Job control : `jobs`, `fg`, `bg`, Ctrl-Z |

## 3. Prérequis

- **Linux, macOS ou WSL** (Ubuntu sous Windows).
- **Python 3.9 ou plus récent** (vérifier avec `python3 --version`).

> `os.fork()` n'existe pas sur Windows natif : PowerShell et CMD ne conviennent pas.
> Aucune bibliothèque externe à installer.

## 4. Installation

Cloner le dépôt et se placer dans le dossier du code :

```bash
git clone https://github.com/malak-elharraoui/SHECODES.git
cd SHECODES/code
```

Si le dossier `SHECODES` existe déjà, mettez-le à jour à la place :

```bash
cd SHECODES
git pull origin main
cd code
```

## 5. Exécution

**Mode interactif** (prompt `opsh>`) :

```bash
python3 main.py
```

**Mode script** (exécute un fichier `.opsh`, puis rend la main) :

```bash
python3 main.py script.opsh
```

Pour quitter le shell : `quit` (ou `Ctrl-D`).

## 6. Commandes disponibles

### 6.1 Builtins

Ils sont exécutés dans le processus du shell lui-même.

| Bash | opsh | Rôle |
|---|---|---|
| `cd` | `go` | changer de dossier (sans argument : dossier personnel) |
| `exit` | `quit` | quitter le shell |
| `pwd` | `path` | afficher le dossier courant |
| `echo` | `say` | afficher du texte |
| `help` | `info` | afficher l'aide |
| `history` | `past` | afficher l'historique |
| `\|` | `->` | pipe |
| — | `osinfo` | affiche `Systèmes d'Exploitation -- UIR/ESIN` |
| `export` | `export` | exporter une variable dans l'environnement |
| `jobs` | `jobs` | lister les jobs |
| `fg` | `fg [%n]` | ramener un job au premier plan |
| `bg` | `bg [%n]` | relancer un job arrêté en arrière-plan |

### 6.2 Alias

Ce sont des programmes Linux lancés avec `fork` + `exec`.

| Bash | opsh |
|---|---|
| `ls` | `list` |
| `cat` | `show` |
| `cp` | `copy` |
| `mv` | `move` |
| `rm` | `del` |
| `mkdir` | `newdir` |
| `touch` | `newfile` |

Toute autre commande (`wc`, `sort`, `grep`, `sleep`, `ps`...) est cherchée dans le `PATH` et exécutée telle quelle.

### 6.3 Opérateurs

| Syntaxe | Effet |
|---|---|
| `cmd > f` | rediriger la sortie vers `f` (écrase) |
| `cmd >> f` | ajouter la sortie à la fin de `f` |
| `cmd < f` | lire l'entrée depuis `f` |
| `cmd1 -> cmd2` | la sortie de `cmd1` devient l'entrée de `cmd2` |
| `cmd &` | exécuter en arrière-plan |
| `$VAR`, `${VAR}` | valeur d'une variable |
| `$?` | code de retour de la dernière commande |
| `$!` | PID du dernier processus lancé en arrière-plan |
| `$$` | PID du shell |
| `$((expr))` | calcul arithmétique |
| `$(cmd)` ou `` `cmd` `` | sortie d'une commande |

## 7. Exemples d'utilisation

### 7.1 Redirections

```
opsh> say hello > f.txt
opsh> say world >> f.txt
opsh> show f.txt
hello
world
opsh> wc -l < f.txt
2
```

`>` crée ou écrase le fichier, `>>` ajoute à la fin, `<` envoie le fichier sur l'entrée de la commande.

### 7.2 Pipes

```
opsh> show f.txt -> wc -l
2
opsh> list -> grep ".py"
main.py
```

### 7.3 Erreurs et codes de retour

```
opsh> commande_inexistante
opsh: command not found: commande_inexistante
opsh> say $?
127
```

## 8. Complétion avec la touche Tab

Tab n'est pas une commande : c'est une **touche à appuyer sans valider avec Entrée**. Elle complète ce que vous avez commencé à écrire :

- **en première position** (le nom de la commande) : elle complète parmi les builtins et les alias ;
- **après le nom de la commande** : elle complète les noms de fichiers et de dossiers (un `/` est ajouté après un dossier).

| Vous tapez | Vous appuyez sur | Résultat |
|---|:---:|---|
| `li` | Tab | `list` |
| `show ma` | Tab | `show main.py` |

S'il y a plusieurs possibilités (par exemple `s` : `say`, `show`), appuyez deux fois sur Tab pour voir la liste.

## 9. Codes de retour

Le code de retour de la dernière commande se lit avec `$?`.

| Code | Signification |
|:---:|---|
| 0 | succès |
| 1 | erreur générale (ex. `go` vers un dossier inexistant) |
| 2 | erreur de syntaxe |
| 126 | commande trouvée mais non exécutable |
| 127 | commande introuvable |
| 128 + N | processus tué par le signal N (130 pour Ctrl-C) |

## 10. Architecture du code

Tout le code est dans `code/main.py`, organisé autour de la classe `Opsh`.

| Partie | Rôle |
|---|---|
| `expand()`, `capture()`, `arith()` | expansion des variables, `$(...)`, backticks, arithmétique |
| `split_pipes()`, `parse_command()` | découpage sur `->`, mots, redirections, `&` |
| `builtin()` | builtins exécutés dans le shell |
| `run_builtin_redirected()` | builtin avec redirection : sauvegarde et restauration des descripteurs |
| `fork_pipeline()` | `fork`, `pipe`, `dup2`, `execvp` pour chaque commande |
| `wait_for()` | `waitpid` avec `WUNTRACED`, détection de Ctrl-Z |
| `on_sigchld()` | récupération des jobs terminés (pas de zombies) |
| `run_foreground()`, `signal_job()`, `give_terminal()` | job control, groupes de processus, `tcsetpgrp` |
| `parse_block()`, `run_nodes()`, `run_script()` | mode script `if` / `for` / `while` |
| `setup_readline()`, `load_rc()` | historique, complétion, `.opshrc` |

**Trajet d'une ligne de commande :**

```
lecture -> historique -> expansion ($VAR, $?, $(..), `..`, $((..)))
        -> découpage sur '->' -> pour chaque commande : mots, > >> < &
        -> builtin ? exécution dans le shell : fork() + execvp()
        -> waitpid (sauf si '&') -> code de retour rangé dans $?
```

## 11. Limites connues

- Pas d'opérateurs `&&`, `||` ni `;` entre commandes (hors `if cmd; then`) : ils sont passés comme de simples arguments (`say a && say b` affiche `a && say b`).
- Pas de redirection de `stderr` (`2>`, `2>&1`) : dans `say x 2> f`, le `2` est lu comme un argument et c'est la sortie standard qui est redirigée.
- Pas d'expansion des jokers (`*`, `?`) ni des accolades (`{a,b}`) : `list *.py` échoue, car `ls` reçoit le texte `*.py` tel quel.
- Dans les scripts, `then`, `do`, `else`, `fi` et `done` doivent être chacun sur leur propre ligne (ou après un `;` : `if cmd; then`).
- Ctrl-Z, `fg` et `bg` ne fonctionnent qu'en mode interactif sur un vrai terminal.

## 12. Contenu du dépôt

```
.
├── code/
│   └── main.py        # le shell opsh
├── report.pdf         # rapport (approche, difficultés, résultats, liens avec le cours)
├── README.md          # ce fichier
└── demo.mp4           # vidéo de démonstration
```
