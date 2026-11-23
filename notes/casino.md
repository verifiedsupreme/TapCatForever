# The TapCat Casino

## Where to find it
- A new Casino tab sits between Shop and Leaderboard in the TapCatForever window.
- The Casino fills the whole window under the tabs. Pick Slots, Blackjack or Death roll with the buttons at the top. The Death roll view also plays rock paper scissors.
- The line at the top shows your bet limits, and your stats for the game you are playing: games played, total bet, paid back, net and your biggest win (hover it for every game).

## Bets
- A bet is at least 10 TapCoins and at most half your TapCoins (rounded down to the bet step). There is no top bet.
- You need at least 20 TapCoins to play.
- The - and + buttons take bigger steps on big bets (100 from 1,000, 250 from 2,500, 500 from 5,000, and so on).
- In a duel with a friend, each of you can bet at most half your own TapCoins, and exactly the bet you both agreed moves between you.
- For the developer: Casino.lua TCF:CasinoLimits (TCF.CASINO_MAX_SHARE = 0.5, TCF.CasinoBetStep), TCF.CASINO_MAX_BET is gone; TCF:CasinoSettleDuel caps the change at the agreed stake; DeathRoll.lua DR.MSG_BET_MAX only turns away absurd numbers in messages.
- Use the - and + buttons or the quick 10, 50, 100 and Max buttons to choose your bet. All the games share the same bet, and it is kept for next time.
- Every game against the house keeps a small house edge, so over time the Casino takes a few TapCoins out of the game. Duels with friends are even: no table fee. It is for fun, not for getting rich. There are no free spins.
- Casino bets and wins don't count toward the TapCoins earned and spent achievements.

## Lucky Paws slots
- A cartoon cat slot machine with three reels. Pull the lever or press Spin.
- The reels spin, slow down and stop from left to right with a little bounce. Click the reels (or press Stop) to land them at once.
- Only the middle line counts. Three of a kind wins, and every cat on the line pays something.
- Pays (times your bet, your bet included): three cats 100, three gems 40, three bells 25, three coins 15, three fish 10, three yarn balls 5, three paws 3, two cats 5, one cat 2.
- The rarer a line, the more it pays: three cats come up about 1 in 1,000 spins, gems 1 in 667, bells 1 in 500, coins 1 in 400, fish 1 in 296, yarn balls 1 in 222 and paws 1 in 178.
- The result line says what you won on top of your bet: "One cat. You win 10 TapCoins" on a bet of 10 (you get 20 back).
- About 3 spins in 10 win something. Over many spins the machine pays back about 94% of what is bet.
- Hover the "How it works" line for the chance of every line.
- A big win (10 times your bet or more) gets a coin shower, flashing lights and a cheer from your cat, inside the window only.

## Blackjack
- Get closer to 21 than the dealer without going over. Picture cards count 10, aces 1 or 11.
- A win pays 1 to 1. A blackjack (an ace and a 10 card as your first two cards) pays 3 to 2, with half a TapCoin rounded down on odd bets. A tie is a push: you get your bet back.
- The dealer draws to 17 and stands on every 17, soft 17 too. The dealer checks for blackjack first.
- Double: double your bet on any first two cards and take exactly one more card.
- Split: split a pair into two hands once. Split aces get one card each.
- No insurance. Six decks, shuffled again when a quarter of the shoe is left.
- With perfect play the house keeps about half a percent.
- Closing the window doesn't lose your hand: it waits for you, even after a reload. A win is always paid, even if you close the window while the cards are still being dealt.

## Achievements
- Natural: get a blackjack (25 TapCoins).
- Three Cats in a Row: line up three cats on the slots (100 TapCoins).

## Death roll
- Two cats take turns rolling. The first roll is 1 to 1,000 (or 100, or 10,000: pick where the rolls start). Each next roll is 1 to the last number rolled. Whoever rolls a 1 loses.
- It plays out in a cosy cartoon cat tavern, by the fire: your cat on the left in its real look, the other cat on the right. Each roll pops up over the roller's head and the range in the middle shrinks. Numbers of 10 and below turn red and shake.
- On a 1 the loser spins and flops onto its back with X eyes, a little ghost cat floats up, and a few seconds later it pops back up, fine. The winner jumps around in confetti.
- A small How to play box above the table explains the rules (hover it to read them as a tooltip too).

## Death roll against the house cat
- Press House cat, choose your bet and where the rolls start, and press Start. The house cat has a fun name and look each game (Lucky Paws is a tuxedo cat).
- A coin flip decides who rolls first, so you win half the games.
- A win gives you 1.9 times your bet back: on a bet of 100 you win 90. Over many games the house keeps about 5% of what is bet.
- A game you leave halfway waits for you, even after a reload.

## Death roll with a friend
- Group up (party or raid) with a friend who has TapCatForever. Press Friend, pick them with the arrows, choose a bet and press Challenge.
- Your friend gets a small Accept or Decline box just above their cat on the screen, and in the Casino tab. It goes away after 60 seconds.
- You both need enough TapCoins for the bet (each player's own limits count). Your bet is held while the duel runs and comes back if it is called off.
- The rolls are real /roll rolls: the Roll button rolls for you, and they also show in chat for your group like a normal /roll. You can type /roll yourself too, as long as it is your turn and the right range.
- Whoever rolls the 1 loses their bet, and the winner gets all of it. There is no table fee between friends.
- Each turn has 60 seconds. If you don't roll in time, you lose the duel, the same as rolling the 1.
- If someone reloads or leaves the group before the 1, or the game hides the roll results, the duel is called off and no TapCoins move.
- Duels with friends don't work inside dungeons, raids, battlegrounds or arenas: the game hides the roll results there. Challenge each other outside.
- Once the 1 has been rolled, the result stands: leaving the group or a reload then doesn't undo it.
- If you decline or don't answer, that friend can challenge you again after 20 seconds.

## Rock paper scissors
- Pick Rock paper scissors under the top bar of the Death roll view (Death roll switches back). It plays out on a snowy mountaintop above the clouds, with little flags blowing in the wind.
- Rock beats scissors, scissors beat paper, paper beats rock. Both cats shake a paw three times ("rock, paper, scissors") and then show their sign: a fist paw, an open paw, or two toes up, drawn in each cat's own fur colour. The winner hops in confetti and the loser flops over, like the death roll.
- A small How to play box explains the rules (hover it for a tooltip too).

## Rock paper scissors against the house cat
- Press House cat, choose your bet and press Rock, Paper or Scissors: that places the bet. The house cat picks at random.
- A tie plays again for free: your bet stays on the table until someone wins.
- A win gives you 1.9 times your bet back: on a bet of 100 you win 90. Ties replay, so you win half the games, and over many games the house keeps about 5% of what is bet, the same as the death roll.
- A game waiting after a tie waits for you, even after a reload.

## Rock paper scissors with a friend
- Press Friend, pick a friend in your party or raid who has TapCatForever with the arrows, choose a bet and press Challenge. They get the same small Accept or Decline box as for a death roll.
- Best of 1, and a tie plays again. You both bet the same amount, and the winner gets the whole bet (no table fee).
- Neither addon can see the other pick first: each one locks in its pick (it sends only a scrambled code of the pick and a random secret), and only when both are locked in do they show their picks, and each checks the other's matches what was locked in.
- If a pick doesn't match what was locked in, or doesn't arrive within 30 seconds, the game is called off and no TapCoins move. The game says why.
- Each pick has 60 seconds. A reload or leaving the group before the result calls the game off, and no TapCoins move.
- Unlike death roll, it works inside dungeons and raids too: it doesn't use /roll.
