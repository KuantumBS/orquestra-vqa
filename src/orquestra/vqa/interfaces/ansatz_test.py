class AnsatzTests(object):
    # To run tests with this base class, the following variables need to be properly initialized in the child class:
    # self.ansatz

    def test_set_n_layers(self):
        # Given
        new_n_layers = 100

        # When
        self.ansatz.n_layers = new_n_layers

        # Then
        self.assertEqual(self.ansatz.n_layers, new_n_layers)

    def test_set_n_qubits_invalidates_circuit(self):
        # Given
        new_n_layers = 100
        new_circuit = self.ansatz.circuit()

        # When
        self.ansatz.n_layers = new_n_layers

        # Then
        self.assertIsNone(self.ansatz._circuit)
