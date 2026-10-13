"""Safety Gateway. 9장에서 추가.

입구(Input Filter)와 출구(Output Filter)에 필터를 세우고, 흩어져 있던 기록을
하나의 요청 ID로 묶는다. LangGraph 흐름 자체는 건드리지 않는다 —
가드레일은 Agent가 무엇을 하든 그 앞뒤에서 걸러야 하는 것이지,
Agent가 협조해 줘야 도는 것이 아니다.
"""