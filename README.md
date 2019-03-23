# basic_limit_order_book

In this repository, I created a basic limit order book.

Methods:

  add_limit_order(side, user_id, quantity, price): places limit order into book
  
  place_market_order(side, quantity): places market order, fulfills as much as possible, removing completed orders from book
  
  cancel_limit_order(order_id): cancels order, removes from book if possible
  
  bbo(): returns best bid offer
