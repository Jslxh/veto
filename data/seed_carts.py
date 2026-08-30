import os
import json

def generate_carts():
    # Define the first 5 original test scenarios exactly as mock client expect them
    carts = [
        {
            "id": "cart_scenario_1",
            "items": [{"id": "item_A", "price": 1200.0, "category": "electronics"}],
            "order_value": 1200.0,
            "customer_id": "cust_1",
            "has_active_discount": False,
            "purchase_history": [],
            "declined_upsells_count": 0,
            "simulate_outcome": None
        },
        {
            "id": "cart_scenario_2",
            "items": [{"id": "item_A", "price": 1200.0, "category": "electronics"}],
            "order_value": 1200.0,
            "customer_id": "cust_1",
            "has_active_discount": False,
            "purchase_history": [],
            "declined_upsells_count": 0,
            "simulate_outcome": {
                "accepted": True,
                "order_value_delta": 250.0
            }
        },
        {
            "id": "cart_scenario_3",
            "items": [{"id": "item_A", "price": 1200.0, "category": "electronics"}],
            "order_value": 1200.0,
            "customer_id": "cust_1",
            "has_active_discount": False,
            "purchase_history": [],
            "declined_upsells_count": 0,
            "simulate_outcome": {
                "accepted": False,
                "order_value_delta": 0.0
            }
        },
        {
            "id": "cart_scenario_4",
            "items": [{"id": "item_C", "price": 500.0, "category": "apparel"}],
            "order_value": 500.0,
            "customer_id": "cust_4",
            "has_active_discount": False,
            "purchase_history": ["apparel"],
            "declined_upsells_count": 2,
            "simulate_outcome": None
        },
        {
            "id": "cart_scenario_5",
            "items": [{"id": "item_A", "price": 1200.0, "category": "electronics"}],
            "order_value": 1200.0,
            "customer_id": "cust_5",
            "has_active_discount": True,
            "purchase_history": [],
            "declined_upsells_count": 0,
            "simulate_outcome": None
        }
    ]

    # Generate 45 additional carts (from index 6 to 50)
    # We want varied values, categories, discounts, declines, rules
    categories = ["electronics", "apparel", "groceries", "home", "beauty", "sports", "books"]
    
    for i in range(6, 51):
        cart_id = f"cart_gen_{i}"
        customer_id = f"cust_gen_{100 + i}"
        
        # Determine value range: spread between 500 and 8000
        # Let's make it a mix of low, medium, and high value carts
        if i % 3 == 0: # High value
            order_value = float(5000 + (i * 57) % 3000)
        elif i % 3 == 1: # Low value
            order_value = float(500 + (i * 23) % 1000)
        else: # Medium value
            order_value = float(1500 + (i * 41) % 3000)
            
        # Determine discount state: ~30% have active discount
        # Active discount for indexes: 7, 10, 13, 17, 20, 23, 27, 30, 33, 37, 40, 43, 47, 50 (approx 14 carts)
        has_active_discount = (i % 3 == 1 and i % 2 == 0) or (i == 50)
        
        # Determine declined upsells count:
        # 0 declines (50%), 1 decline (30%), 2+ declines (20%)
        if i % 10 in [0, 1]:
            declined_upsells_count = 2 # 2 declines
        elif i % 10 == 2:
            declined_upsells_count = 3 # 2+ declines
        elif i % 10 in [3, 4, 5]:
            declined_upsells_count = 1 # 1 decline
        else:
            declined_upsells_count = 0 # 0 declines

        # Items construction based on which rule we want to target or trigger
        # We target different rules based on index
        items = []
        purchase_history = []
        
        rule_target = i % 4
        if rule_target == 0:
            # Target bundle_completion: has item_A, no item_B, order value >= 1000
            # To ensure value matches we make it item_A + some other item
            price_a = min(order_value - 100.0, 1200.0)
            items.append({"id": "item_A", "price": price_a, "category": "electronics"})
            if order_value > price_a:
                items.append({"id": f"item_other_{i}", "price": order_value - price_a, "category": "home"})
        elif rule_target == 1:
            # Target high_value_threshold: order_value >= 5000
            # Let's ensure value is indeed >= 5000
            if order_value < 5000:
                order_value += 4500.0
            items.append({"id": f"item_high_{i}", "price": order_value, "category": "electronics"})
        elif rule_target == 2:
            # Target repeat_customer_affinity: category match in purchase history
            cat = categories[i % len(categories)]
            items.append({"id": f"item_aff_{i}", "price": order_value, "category": cat})
            purchase_history.append(cat)
            # Add some other category to history
            purchase_history.append(categories[(i + 1) % len(categories)])
        else:
            # Target no rule matched: low value, no item_A, no matching purchase history
            if order_value >= 5000:
                order_value = float(800 + i) # make it low value
            cat = categories[i % len(categories)]
            items.append({"id": f"item_no_{i}", "price": order_value, "category": cat})
            # Purchase history doesn't match item category
            non_matching_cat = categories[(i + 1) % len(categories)]
            purchase_history.append(non_matching_cat)

        # Build simulated outcomes for proposed ones (not already discounted and declines < 2)
        # Let's make it realistic: if the customer has 0 declines, they accept 70% of the time,
        # 1 decline -> 40% accept, 2+ declines -> never accepts (or already below threshold)
        simulate_outcome = None
        if not has_active_discount and declined_upsells_count < 2:
            # Determine acceptance deterministically so it's stable and reproducible
            is_accepted = (i % 2 == 0) if declined_upsells_count == 0 else (i % 3 == 0)
            if is_accepted:
                # Delta is ~15% of order value, rounded to 2 decimals
                delta = round(order_value * 0.15, 2)
                simulate_outcome = {
                    "accepted": True,
                    "order_value_delta": delta
                }
            else:
                simulate_outcome = {
                    "accepted": False,
                    "order_value_delta": 0.0
                }

        carts.append({
            "id": cart_id,
            "items": items,
            "order_value": order_value,
            "customer_id": customer_id,
            "has_active_discount": has_active_discount,
            "purchase_history": purchase_history,
            "declined_upsells_count": declined_upsells_count,
            "simulate_outcome": simulate_outcome
        })

    # Create directories if they do not exist
    os.makedirs("data", exist_ok=True)
    
    # Save to data/carts.json
    with open("data/carts.json", "w") as f:
        json.dump(carts, f, indent=2)
        
    print(f"Successfully generated {len(carts)} synthetic carts in data/carts.json")

if __name__ == "__main__":
    generate_carts()
