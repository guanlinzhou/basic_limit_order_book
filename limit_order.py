'''
A few implementation ideas here:

1. Order Book, [] indexed by order_id.
    Pros:
    1. Constant add_limit_order
    2. cancel_limit_order also constant, just index in by order_id
    3.
    Cons:
    Many technicalities when trying to Cancel Order. Obviously cannot reindex the order ID, so must do something else.
    When an order is removed, if set to None, lots of error checking required and space complexity for the array bad.
    If removed from array then the indexing property is destroyed, and accessing becomes linear for search for order id.

2. Order Book {'ask':[], 'bid':[]}
    Similar to last approach, but easier side access and harder order_id accessing.

3. Order Book {'ask':{}, 'bid':{}}: May be best, hashed for best runtime dictionaries are hashed, best for lookup by next_order_id
    Ideas:
        Min/Max Heap for market orders
        Access same order by order_id and price, tiebreak on price can be arbitrary (only used in market orders).

USED IMPLEMENTATION 3

Want to implement some sort of min/max_heap to make runtime of the update functions better.
Update performs on each add/cancel and on each place_market_order.

FINAL IMPLEMENTATION NOTES:

    Structure:
        1. order_book: {'ask':{}, 'bid':{}}
            Inner dictionaries hashed by order_id

        2. min_heap and max_heap: loosely maintained invariant with lazy evaluation
            Top always min/max but sometimes top should have already been removed
            In this case, it will be removed on an error check before continuing

        3. price_to_order: dictionary/hash table with key: price and value: next_order_id
            Enables access to order_book using price in O(1) runtime

        4. fulfilled: set of fulfilled orders
            small quality of life improvement when attempting to cancel

    Runtime Analysis:

        add_limit_order:
            Amortized: O(1) insert, worst case O(n) but only when entire min/max heap is invalid (extremely rare case)

        place_market_order:
            Really depends on size of order (s) and average quantity of each item (q), for most small orders will be O(1),
            but general runtime O(s/q)

        cancel_limit_order:
            Amortized: O(1) removal, worst case O(n) but only when entire min/max heap is invalid (extremely rare case)

        bbo:
            Amortized O(1), worst case O(n) but only when entire min/max heap is invalid (extremely rare case)

'''


import heapq as pq

class order_book:

    def __init__(self):
        self.next_order_id = 1
        self.order_book = {'ask':{},'bid':{}}
        self.max_heap = []
        self.min_heap = []
        self.price_to_order = {}
        self.fulfilled = set()



    # Adds Order to Book, increments order ID
    #Helper: update_bbo_when_add
    def add_limit_order(self, side, user_id, quantity, price):
        order_id = self.next_order_id
        self.order_book[side][self.next_order_id] = {'order_id': order_id, 'side':side, 'user_id':user_id, 'quantity':quantity, 'price':price}
        self.price_to_order[price] = order_id
        self.next_order_id += 1
        self.update_bbo_when_add(side, price)
        return order_id



    # Places a market order and fulfills as much as possible
    # Helper: update_bbo_when_market
    # Outputs: [quantity of order filled, average price of order filled]
    def place_market_order(self, side, quantity):
        qty_remain, total_price = self.update_bbo_when_market(side, quantity)
        qty_filled = quantity - qty_remain
        return [qty_filled, total_price/qty_filled]


    # def place_market_order(self, side, quantity):
    #     to_delete = []
    #     partial_delete = None
    #     total_price = 0
    #     qty_filled = 0
    #     if side == 'ask':
    #         without_delete = self.order_book
    #         without_delete.sort(key=self.price)
    #     if side == 'bid':
    #         without_delete = self.order_book
    #         without_delete.sort(key=self.price, reverse=True)
    #     while quantity > 0 and len(to_delete) < len(self.order_book):
    #         if side == 'ask':
    #             if without_delete[0]['side'] == 'ask':
    #                 if quantity < without_delete[0]['quantity']:
    #                     partial_delete = without_delete[0]['order_id'], without_delete[0]['quantity'] - quantity
    #                     total_price += without_delete[0]['price'] * quantity
    #                     qty_filled += quantity
    #                     without_delete[0]['quantity'] -= quantity
    #                     quantity = 0
    #                 else:
    #                     total_price += without_delete[0]['price'] * without_delete[0]['quantity']
    #                     qty_filled += without_delete[0]['quantity']
    #                     quantity -= without_delete[0]['quantity']
    #                     to_delete.append(without_delete[0])
    #             without_delete = without_delete[1:]
    #         if side == 'bid':
    #             if without_delete[0]['side'] == 'bid':
    #                 if quantity < without_delete[0]['quantity']:
    #                     partial_delete = without_delete[0]['order_id'], without_delete[0]['quantity'] - quantity
    #                     without_delete[0]['quantity'] -= quantity
    #                     quantity = 0
    #                 else:
    #                     quantity -= without_delete[0]['quantity']
    #                     to_delete.append(without_delete[0])
    #             without_delete = without_delete[1:]
    #     for n in self.order_book:
    #         if n in without_delete:
    #             i = self.order_book.index(n)
    #             self.order_book[i] = None
    #     return [qty_filled, total_price/qty_filled]



    # Maintains heap invariant and weeds out cancelled orders from heaps
    def maintain_heap_invariant(self):

        # This function handles the case in which a price is not taken off the heap after
        # the order was cancelled. It maintains the validity of the top of the heap by checking
        # the top of the heap against existing orders to make sure that the top of the heap
        # is a currently valid order.

        while self.max_heap != [] and self.max_heap[0] not in self.price_to_order:
            pq.heappop(self.max_heap)
        while self.min_heap != [] and self.min_heap[0] not in self.price_to_order:
            pq.heappop(self.min_heap)



    # Cancels order (removes from book), gives error messages if not possible
    # Helper: update_bbo_when_cancel
    def cancel_limit_order(self, order_id):
        if order_id in self.order_book['bid']:
            side = 'bid'
        elif order_id in self.order_book['ask']:
            side = 'ask'
        elif order_id in self.fulfilled:
            print('Order Fulfilled: Unable to Cancel')
            return
        else:
            print('Order not found -- please verify order ID')
            return
        price = self.order_book['side'][order_id]['price']
        self.order_book[side].pop(order_id)
        self.update_bbo_when_cancel(side, price)



    # Push new price onto appropriate heap upon adding new order
    def update_bbo_when_add(self, side, price):
        self.maintain_heap_invariant()
        if side == "ask":
            pq.heappush(self.min_heap, price)
        if side == "bid":
            pq.heappush(self.max_heap, -price)


    # Remove price from top of heap, if it is at the Top, when cancelling
    def update_bbo_when_cancel(self, side, price):
        self.maintain_heap_invariant()
        if side == "bid":
            if -price == self.max_heap[0]:
                pq.heappop(self.max_heap)
            self.price_to_order.pop(price)
        if side == "ask":
            if price == self.min_heap[0]:
                pq.heappop(self.min_heap)
            self.price_to_order.pop(price)


    # Handles market orders, more comments in function
    # Outputs: [Quantity Remaining, Total Price Fulfilled]
    def update_bbo_when_market(self, side, qty):
        self.maintain_heap_invariant()
        if side == 'bid':

            #If desired quantity = 0 or order book is empty, end function
            if self.order_book[side] == {} or qty == 0:
                return qty, 0

            curr_qty = self.order_book[side][self.price_to_order[-self.max_heap[0]]]['quantity']

            # If desired quantity is larger than quantity in the best order,
            # remove this order and recurse on the rest of the quantity
            if qty >= curr_qty:
                price = pq.heappop(self.max_heap)
                order_id = self.price_to_order.pop(price)
                self.order_book[side].pop(order_id)
                self.fulfilled.add(order_id)
                next = self.update_bbo_when_market(side, qty-curr_qty)
                return next[0], price * curr_qty + next[1]

            # If desired qty is less than qty of order, remove qty from this order, end function
            else:
                price = self.max_heap[0]
                order_id = self.price_to_order[price]
                self.order_book[side][order_id]['quantity'] -= qty
                return 0, price * qty
        if side == 'ask':

            #If desired quantity = 0 or order book is empty, end function
            if self.order_book[side] == {} or qty == 0:
                return qty, 0

            curr_qty = self.order_book[side][self.price_to_order[self.min_heap[0]]]['quantity']

            # If desired quantity is larger than quantity in the best order,
            # remove this order and recurse on the rest of the quantity
            if qty >= curr_qty:
                price = pq.heappop(self.min_heap)
                order_id = self.price_to_order.pop(price)
                self.order_book[side].pop(order_id)
                self.fulfilled.add(order_id)
                next = self.update_bbo_when_market(side, qty-curr_qty)
                return next[0], price * curr_qty + next[1]

            # If desired qty is less than qty of order, remove qty from this order, end function
            else:
                price = self.min_heap[0]
                order_id = self.price_to_order[price]
                self.order_book[side][order_id]['quantity'] -= qty
                return 0, price * qty



    # Returns Best Bid Offer
    def bbo(self):
        self.maintain_heap_invariant()
        print([self.max_heap[0], self.min_heap[0]])



if __name__ == '__main__':
    # Testing
    lob_example = order_book()
    lob_example.add_limit_order('ask', 'alice', 10, 100)
    lob_example.add_limit_order('ask', 'bob', 5, 90)
    lob_example.add_limit_order('bid', 'charles', 20, 85)
    lob_example.add_limit_order('bid', 'dave', 10, 80)
    print(lob_example.order_book)
    lob_example.add_limit_order('ask', 'eve', 10, 95)
    print(lob_example.place_market_order('ask', 12))
    print(lob_example.order_book)
    print(lob_example.place_market_order('ask', 90))
    print(lob_example.order_book)
    lob_example.cancel_limit_order(2)
    lob_example.cancel_limit_order(26)
