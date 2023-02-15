import time
from ws import BetBryClientAPI, result_dict


if __name__ == '__main__':
    bba = BetBryClientAPI()
    # bba.preview = True
    # bba.trace_route = True
    bba.set_headers()
    bba.connect()

    created = None
    while True:
        if len(result_dict) > 0:
            if result_dict[-1].get("created") != created:
                created = result_dict[-1].get("created")
                print(result_dict)
        time.sleep(10)
