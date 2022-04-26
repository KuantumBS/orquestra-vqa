################################################################################
# © Copyright 2021-2022 Zapata Computing Inc.
################################################################################


def allocate_shots_uniformly(
    estimation_tasks: List[EstimationTask], number_of_shots: int
) -> List[EstimationTask]:
    """
    Allocates the same number of shots to each task.

    Args:
        number_of_shots: number of shots to be assigned to each EstimationTask
    """
    if number_of_shots <= 0:
        raise ValueError("number_of_shots must be positive.")

    return [
        EstimationTask(
            operator=estimation_task.operator,
            circuit=estimation_task.circuit,
            number_of_shots=number_of_shots,
        )
        for estimation_task in estimation_tasks
    ]


def allocate_shots_proportionally(
    estimation_tasks: List[EstimationTask],
    total_n_shots: int,
    prior_expectation_values: Optional[ExpectationValues] = None,
) -> List[EstimationTask]:
    """Allocates specified number of shots proportionally to the variance associated
    with each operator in a list of estimation tasks. For more details please refer to
    the documentation of `zquantum.core.hamiltonian.estimate_nmeas_for_frames`.

    Args:
        total_n_shots: total number of shots to be allocated
        prior_expectation_values: object containing the expectation
            values of all operators in frame_operators
    """
    if total_n_shots <= 0:
        raise ValueError("total_n_shots must be positive.")

    frame_operators = [
        cast(QubitOperator, estimation_task.operator)
        for estimation_task in estimation_tasks
    ]

    _, _, relative_measurements_per_frame = estimate_nmeas_for_frames(
        frame_operators, prior_expectation_values
    )

    measurements_per_frame = scale_and_discretize(
        relative_measurements_per_frame, total_n_shots
    )

    return [
        EstimationTask(
            operator=estimation_task.operator,
            circuit=estimation_task.circuit,
            number_of_shots=number_of_shots,
        )
        for estimation_task, number_of_shots in zip(
            estimation_tasks, measurements_per_frame
        )
    ]


def estimate_nmeas_for_frames(
    frame_operators: List[QubitOperator],
    expecval: Optional[ExpectationValues] = None,
) -> Tuple[float, int, np.ndarray]:
    r"""Calculates the number of measurements required for computing
    the expectation value of a qubit hamiltonian, where co-measurable terms
    are grouped in a single QubitOperator, and different groups are different
    members of the list.

    We are assuming the exact expectation values are provided
    (i.e. infinite number of measurements or simulations without noise)
    M ~ (\sum_{i} prec(H_i)) ** 2.0 / (epsilon ** 2.0)
    where prec(H_i) is the precision (square root of the variance)
    for each group of co-measurable terms H_{i}. It is computed as
    prec(H_{i}) = \sum{ab} |h_{a}^{i}||h_{b}^{i}| cov(O_{a}^{i}, O_{b}^{i})
    where h_{a}^{i} is the coefficient of the a-th operator, O_{a}^{i}, in the
    i-th group. Covariances are assumed to be zero for a != b:
    cov(O_{a}^{i}, O_{b}^{i}) = <O_{a}^{i} O_{b}^{i}> - <O_{a}^{i}> <O_{b}^{i}> = 0

    Args:
        frame_operators (List[QubitOperator]): A list of QubitOperator objects, where
            each element in the list is a group of co-measurable terms.
        expecval (Optional[ExpectationValues]): An ExpectationValues object containing
            the expectation values of all operators in frame_operators. If absent,
            variances are assumed to be maximal, i.e. 1.
            NOTE: YOU HAVE TO MAKE SURE THAT THE ORDER OF EXPECTATION VALUES MATCHES
            THE ORDER OF THE TERMS IN THE *GROUPED* TARGET QUBIT OPERATOR, OTHERWISE
            THIS FUNCTION WILL NOT RETURN THE CORRECT RESULT.

    Returns:
        K2 (float): number of measurements for epsilon = 1.0
        nterms (int): number of groups in frame_operators
        frame_meas (np.array): Number of optimal measurements per group
    """
    frame_variances = compute_group_variances(frame_operators, expecval)
    sqrt_lambda = sum(np.sqrt(frame_variances))
    frame_meas = sqrt_lambda * np.sqrt(frame_variances)
    K2 = sum(frame_meas)
    nterms = sum([len(group.terms) for group in frame_operators])

    return K2, nterms, frame_meas
