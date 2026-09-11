'''
A simple LangGraph program that repeatedly doubles a number until it reaches
or exceeds 100, then moves to the finish node and ends the workflow.
'''

from typing import TypedDict
from langgraph.graph import StateGraph, END

# State of the Graph (represented in Dictionary)
class State(TypedDict):
    number: int

# Nodes of the Graph
def double(state: State) -> dict:
    """
    Doubles the current number stored in the graph state.
    """
    current_num = state["number"]
    new_num = current_num * 2

    print("Node: Double")
    print("Number: ", new_num)

    return {"number": new_num}


def finish(state: State) -> dict:
    """
    Handles the final state of the workflow and returns the current number.
    """
    current_num = state["number"]

    print("Node: Finish")
    print("Number: ", current_num)

    return {"number": current_num}


def decision_maker(state: State) -> str:
    """
    Determines whether the workflow should continue or proceed to completion.
    """
    current_num = state["number"]

    if current_num < 100:
        return "double"
    else:
        return "finish"

# Initialize the Graph
builder = StateGraph(State)

builder.add_node("double", double)
builder.add_node("finish", finish)

builder.set_entry_point("double")

builder.add_conditional_edges(
    "double",
    decision_maker,
    {
        "double": "double",
        "finish": "finish"
    },
)

builder.add_edge(
    "finish",
    END
)


# Create Graph
graph= builder.compile()


if __name__ == "__main__":
    print("-" * 80)
    print("Simple Graph Implementation (& Execution) in LangGraph")
    print("-" * 80)

    intia_num_state = 3
    print("Intial Number State: ", intia_num_state)

    result = graph.invoke({
        "number": intia_num_state
    })

    print("\nFinal Result:", result)

