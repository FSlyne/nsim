from automaton import machines


def print_on_enter(new_state, triggered_event):
   print("Entered '%s' due to '%s'" % (new_state, triggered_event))


def print_on_exit(old_state, triggered_event):
   print("Exiting '%s' due to '%s'" % (old_state, triggered_event))

# This will contain all the states and transitions that our machine will
# allow, the format is relatively simple and designed to be easy to use.
state_space = [
    {
        'name': 'stopped',
        'next_states': {
            # On event 'play' transition to the 'playing' state.
            'play': 'playing',
            'open_close': 'opened',
            'stop': 'stopped',
        },
        'on_enter': print_on_enter,
        'on_exit': print_on_exit,
    },
    {
        'name': 'opened',
        'next_states': {
            'open_close': 'closed',
        },
        'on_enter': print_on_enter,
        'on_exit': print_on_exit,
    },
    {
        'name': 'closed',
        'next_states': {
            'open_close': 'opened',
            'cd_detected': 'stopped',
        },
        'on_enter': print_on_enter,
        'on_exit': print_on_exit,
    },
    {
        'name': 'playing',
        'next_states': {
            'stop': 'stopped',
            'pause': 'paused',
            'open_close': 'opened',
        },
        'on_enter': print_on_enter,
        'on_exit': print_on_exit,
    },
    {
        'name': 'paused',
        'next_states': {
            'play': 'playing',
            'stop': 'stopped',
            'open_close': 'opened',
        },
        'on_enter': print_on_enter,
        'on_exit': print_on_exit,
    },
]

m = machines.FiniteMachine.build(state_space)
m.default_start_state = 'closed'

m.initialize()

print(m.pformat())

for event in ['cd_detected', 'play', 'pause', 'play', 'stop',
              'open_close', 'open_close']:
    m.process_event(event)
    print(m.pformat())
    print("=============")
    print("Current state => %s" % m.current_state)
    print("=============")
