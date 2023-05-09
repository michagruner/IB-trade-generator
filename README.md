# IB-trade-generator
Creates trades via quatr/flask web frontend with a specified risk/reward and sends them to the local TWS api via the great ib_insync library.

steps to get going:
1. download this archive 
2. run "docker-compose build"
3. run "docker-compose up"
4. access http://localhost:5000 with your browser

##Ok, so what is this for?
It is just a demonstration of what you can do with Chat-GPT (I think the model version was 3.5 at that time). ;) So 4 weeks ago I had no clue about flask/quatr or async anything. I just asked Chat-GPT to help me develop an idea and here we are. So take the whole thing as a proof of concept, not production ready obviously. ;)

##Ok, tell me, what is this for?
Ok, you really wanted to know, let's go. I just did some fun research into how one could probably consistently make money in trading. It turned out: it's not an easy task to begin with (I guess you know this already). So you either must have a very high win rate by spoting the fulcrums in a market or you have a good risk/reward. I won't cover how to spot turning points in a market. I advise you to do some research about market structure, trading ranges and market internals for that.

This web app covers the risk/reward part. So the idea is: you provide an invalidation point of your idea (so which point the market should not reach in order to keep your trade-idea alive), your high probability target (target setting is a craft on its own, did I mention that already?), your risk appetite in USD (USD because we trade the E-Mini Future, the worlds most liquid Future contract here) and your destined reward multiple (it should be at least 2 to become profitable, a 1:2 risk/reward allows you to mess up every second trade and still make money on it). Now the software optimizes these parameters and returns:

- The entry limit that you need at least to achieve your risk/reward multiple on the trade
- The number of contracts you need to buy/sell
- The limit and number of contracts for the 1R-Scale out (we take 1/4 of our original size of at 1R, by doing this we reduce our maximum loss on the whole idea to 50%, so when you risk 200 USD on the idea, scaled out and your original stop gets hit you will only loose 100 USD overall [you won 50 and you only get stopped on the remaining 3/4 of your original position])
- The number of contracts that closes your position on your target

You could run this either standalone without anything (you then would have to specify the contract details) or you could use it with a locally runing IB TWS. Using it with a TWS has the advantage that your trades get placed as soon as you hit the "Submit-Trade" button. I advise you to try this with a paper trading account first.

OK, that's it. I hope you have some fun with it and probably make some money, too! ;)

Did I mention that this comes with no warranty whatsoever?
