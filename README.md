# LoupsGaroupVsVampires


Ce projet implémente une IA qui joue au jeu VampireVSWerewolf

Pour lancer l'IA il suffit d'exécuter la commande `python main.py localhost 5555`

# Principe de fonctionnement de l'IA 

L'IA est basée sur un algorithme d'élagage alpha-béta de profondeur 4.

Un des challenges de l'IA était de réduire le nombre de coups considéré par l'IA dans l'arbe d'exploration du jeu. En effet, pour une position donnée, un joueur peut parfois avoir plusieurs milliers de coups possible ce qui rend la simulation impossible pour l'algorithme alpha-béta car nécissant beaucoup trop de temps de calcul pour atteindre une profondeur d'arbre intéressante.

Nous avons alors restreint les coups considérés par l'IA de la manière suivante:
- un joueur ne peut pas séparer ses jetons si il possède déjà deux groupes de jetons, ainsi un joeur ne avoir qu'au maximum deux groupes de jetons
- un joueur ne peut pas déplacer ses jetons dans une direction de "fuite", c'est à dire qu'il ne peut déplacer ses jetons que s'ils se dirigent vers de jetons enemis ou des humains

En appliquant ces hypothèses fortes, on obtient alors un jeu avec quelques dizaines de coups possibles par tour de jeu, ce qui permet d'utiliser l'algorithme alpha-beta pour le jeu.

Le jeu étant probabiliste, nous devions aussi considérer des noeuds aléatoires dans notre arbre alpha-béta. Nous avons choisi de prendre l'esperance des scores de tous les noeuds possible comme le score du noeud probabiliste

Ensuite nous avons du choisir une heuristique pour évaluer un plateau de jeu, nous avons concu notre heuristique de la manière suivante:
- on calcule un premier score qui comporte 2 termes: le premier proportionnel à la différence de nombre de jeton entre les 2 joueurs et un second terme qui dépend de la distance des jetons aux groupes d'humains. Le second terme est nécessaire pour inciter l'IA à se rapprocher des groupes d'humain, car la profondeur de 4 ne permet pas à l'IA de comprendre qu'elle doit se déplacer vers les humains si ceux-ci sont à plus de 4 cases.
- Pour obtenir notre heuristique, nous appliquons la fonction tangeante hyperbolique à ce premier score, car nous considérons que notre IA doit être averse au risque lorsqu'elle possède un avantage et doit choisir de prendre des risques si elle est en mauvaise posture car elle a rien à perdre. Ces valeurs sont importantes en raison des noeuds probabilistes.

Enfin, en developpant notre IA nous avons parfois observé que l'IA avait un comportement attentiste: si l'IA savait qu'elle pouvait gagner, elle ne choisissait pas forcément le chemin le plus court vers la victoire ou même jouer des coups aléatoires en boucle car elle "sait" qu'elle peut toujours gagner au tour suivant. Pour inciter l'IA à choisir le chemin le plus court nous avons alors utilisé un coefficient GAMMA légerement inférieur à 1 que nous multiplions au score obtenu pour les profondeurs inférieurs de sorte, indiquant de fait qu'une victoire atteinte en 2 coups est plus intéressante qu'une victoire en 3 coups.
