'''
Written by Duc
Apr, 2016
Updates on Feb 3, 2017
Updates on Feb 25, 2017: AdaMax, Adam
Major updates on Sep 8, 2017: All algorithms now return updates in OrderedDict (inspired by and collected from Lasagne)
'''

import theano
from theano import tensor as T
import numpy as np
from collections import OrderedDict


class VanillaSGD(object):
    def __init__(self, alpha):
        self.alpha = T.cast(T.as_tensor_variable(alpha), theano.config.floatX)
        print('@ VANILLA GRADIENT DESCEND. ETA = %s ALPHA = %s ' % alpha)

    def get_updates(self, params, grads):
        updates = OrderedDict()
        for param, grad in zip(params, grads):
            updates[param] = param - self.alpha * grad
        return updates


class AdaDelta(object):
    """
        rho: decay rate (usually >0.9 and <1)
    epsilon: constant (usually 1e-8 ~ 1e-4)
    parameters: all weights of the network
    grad: gradient from T.grad
    Example:
        delta = AdaDelta(0.95, 0.000001, parameters=params)
        grads = T.grad(cost, params)
        updates = [
            (param_i, param_i - grad_i)
            for param_i, grad_i in zip(params, delta.deltaXt(grads))
        ]
    """

    def __init__(self, rho, epsilon):
        # self.Eg2 = [T.zeros(p.get_value().shape, dtype=theano.config.floatX) for p in parameters]
        # self.Edelx2 = [T.zeros(p.get_value().shape, dtype=theano.config.floatX) for p in parameters]
        # self.prev_del = [T.zeros(p.get_value().shape, dtype=theano.config.floatX) for p in parameters]
        self.rho = T.as_tensor_variable(np.cast[theano.config.floatX](rho))
        self.epsilon = T.as_tensor_variable(np.cast[theano.config.floatX](epsilon))
        print('@ ADADELTA. RHO = %s EPSILON = %s ' % (self.rho, self.epsilon))

    def get_updates(self, params, grads):
        updates = OrderedDict()
        # Eg2 = [T.zeros(p.get_value().shape, dtype=theano.config.floatX) for p in params]
        # Edelx2 = [T.zeros(p.get_value().shape, dtype=theano.config.floatX) for p in params]
        # prev_del = [T.zeros(p.get_value().shape, dtype=theano.config.floatX) for p in params]
        # Eg2 = [self.rho*Eg2_i + (1. - self.rho)*grad_i**2 for Eg2_i, grad_i in zip(Eg2, grad)]
        # delta = [T.sqrt(prev_del2_i + self.epsilon) / T.sqrt(grad2_i + self.epsilon) * grad_i
        #          for prev_del2_i, grad2_i, grad_i in zip(Edelx2, Eg2, grads)]
        # Edelx2 = [self.rho*delx2_i + (1. - self.rho)*delta_i**2 for delx2_i, delta_i in zip(Edelx2, delta)]
        for param, grad in zip(params, grads):
            Eg2_i = T.zeros(param.get_value().shape, dtype=theano.config.floatX)
            prev_delta_i = T.zeros(param.get_value().shape, dtype=theano.config.floatX)
            Edelx2_i = T.zeros(param.get_value().shape, dtype=theano.config.floatX)
            delta_i = T.sqrt(Edelx2_i + self.epsilon) / T.sqrt(Eg2_i + self.epsilon) * grad
            updates[param] = param - delta_i
            updates[prev_delta_i] = delta_i
            updates[Edelx2_i] = self.rho * Edelx2_i + (1. - self.rho) * delta_i**2
            updates[Eg2_i] = self.rho * Eg2_i + (1. - self.rho) * grad**2
        return updates


class SGDMomentum(object):
    def __init__(self, lr, mom, nesterov=False):
        # self.prev_delta = [T.zeros(p.get_value().shape, dtype=theano.config.floatX) for p in parameters]
        self.eta = T.cast(T.as_tensor_variable(lr), dtype=theano.config.floatX)
        self.alpha = T.cast(T.as_tensor_variable(mom), dtype=theano.config.floatX)
        self.nesterov = nesterov
        print('@ STOCHASTIC GRADIENT DESCENT MOMENTUM. LEARNING RATE = %s MOMENTUM = %s NESTEROV = %s'
              % (lr, mom, nesterov))

    def get_updates(self, params, grads):
        updates = OrderedDict()
        for param, grad in zip(params, grads):
            updates[param] = param - self.eta * grad
        if not self.nesterov:
            updates = self.apply_momentum(updates)
        else:
            updates = self.apply_nesterov_momentum(updates)
        # delta = [self.eta * grad_i + self.alpha * prev_grad_i for grad_i, prev_grad_i in zip(grad, self.prev_delta)]
        # self.prev_delta = delta
        return updates

    def apply_momentum(self, updates):
        """Returns a modified update dictionary including momentum

        Generates update expressions of the form:

        * ``velocity := momentum * velocity + updates[param] - param``
        * ``param := param + velocity``

        Parameters
        ----------
        updates : OrderedDict
            A dictionary mapping parameters to update expressions
        params : iterable of shared variables, optional
            The variables to apply momentum to. If omitted, will apply
            momentum to all `updates.keys()`.
        momentum : float or symbolic scalar, optional
            The amount of momentum to apply. Higher momentum results in
            smoothing over more update steps. Defaults to 0.9.

        Returns
        -------
        OrderedDict
            A copy of `updates` with momentum updates for all `params`.

        Notes
        -----
        Higher momentum also results in larger update steps. To counter that,
        you can optionally scale your learning rate by `1 - momentum`.

        See Also
        --------
        momentum : Shortcut applying momentum to SGD updates
        """
        params = updates.keys()
        updates = OrderedDict(updates)

        for param in params:
            value = param.get_value(borrow=True)
            velocity = theano.shared(np.zeros(value.shape, dtype=value.dtype),
                                     broadcastable=param.broadcastable)
            x = self.alpha * velocity + updates[param]
            updates[velocity] = x - param
            updates[param] = x

        return updates

    def apply_nesterov_momentum(self, updates):
        """Returns a modified update dictionary including Nesterov momentum

        Generates update expressions of the form:

        * ``velocity := momentum * velocity + updates[param] - param``
        * ``param := param + momentum * velocity + updates[param] - param``

        Parameters
        ----------
        delta : OrderedDict
            A dictionary mapping parameters to update expressions
        params : iterable of shared variables, optional
            The variables to apply momentum to. If omitted, will apply
            momentum to all `updates.keys()`.
        momentum : float or symbolic scalar, optional
            The amount of momentum to apply. Higher momentum results in
            smoothing over more update steps. Defaults to 0.9.

        Returns
        -------
        OrderedDict
            A copy of `updates` with momentum updates for all `params`.

        Notes
        -----
        Higher momentum also results in larger update steps. To counter that,
        you can optionally scale your learning rate by `1 - momentum`.

        The classic formulation of Nesterov momentum (or Nesterov accelerated
        gradient) requires the gradient to be evaluated at the predicted next
        position in parameter space. Here, we use the formulation described at
        https://github.com/lisa-lab/pylearn2/pull/136#issuecomment-10381617,
        which allows the gradient to be evaluated at the current parameters.

        See Also
        --------
        nesterov_momentum : Shortcut applying Nesterov momentum to SGD updates
        """
        params = updates.keys()
        updates = OrderedDict(updates)

        for param in params:
            value = param.get_value(borrow=True)
            velocity = theano.shared(np.zeros(value.shape, dtype=value.dtype),
                                     broadcastable=param.broadcastable)
            x = self.alpha * velocity + updates[param] - param
            updates[velocity] = x
            updates[param] = self.alpha * x + updates[param]

        return updates


class AdaGrad(object):
    def __init__(self, eta, epsilon=1e-6):
        self.eta = T.cast(T.as_tensor_variable(eta), theano.config.floatX)
        self.epsilon = T.cast(T.as_tensor_variable(epsilon), theano.config.floatX)
        # self.G = [T.zeros(p.get_value().shape, dtype=theano.config.floatX) for p in parameters]
        print('# ADAGRAD. ETA = %s ' % eta)

    def get_updates(self, params, grads):
        updates = OrderedDict()
        for param, grad in zip(params, grads):
            G = T.zeros(param.get_value().shape, dtype=theano.config.floatX)
            updates[G] = G + grad**2
            updates[param] = self.eta * grad / T.sqrt(self.epsilon + G)
        # G = [g_i + grad_i**2 for g_i, grad_i in zip(G, grad)]
        # delta = [self.eta * grad_i / T.sqrt(self.epsilon + g_i) for grad_i, g_i in zip(grad, self.G)]
        return updates


class RMSprop(object):
    def __init__(self, eta=1e-3, gamma=0.9, epsilon=1e-6):
        self.eta = T.cast(T.as_tensor_variable(eta), theano.config.floatX)
        self.gamma = T.cast(T.as_tensor_variable(gamma), theano.config.floatX)
        self.epsilon = T.cast(T.as_tensor_variable(epsilon), theano.config.floatX)
        # self.Eg2 = [T.zeros(p.get_value().shape, dtype=theano.config.floatX) for p in parameters]
        print('# RMSPROP. ETA = %s GAMMA = %s ' % (eta, gamma))

    def get_updates(self, params, grads):
        updates = OrderedDict()
        # Eg2 = [T.zeros(p.get_value().shape, dtype=theano.config.floatX) for p in params]
        # Eg2 = [self.gamma * Eg2_i + (1. - self.gamma) * grad_i ** 2 for Eg2_i, grad_i in zip(Eg2, grads)]
        # delta = [self.eta * grad_i / T.sqrt(Eg2_i + self.epsilon) for grad_i, Eg2_i in zip(grads, Eg2)]
        for param, grad in zip(params, grads):
            Eg2 = T.zeros(param.get_value().shape, dtype=theano.config.floatX)
            updates[Eg2] = self.gamma * Eg2 + (1. - self.gamma) * grad ** 2
            updates[param] = param - self.eta * grad / T.sqrt(Eg2 + self.epsilon)
        return updates


class Adam(object):
    def __init__(self, alpha=1e-3, beta1=0.9, beta2=0.999, epsilon=1e-8):
        self.alpha = T.cast(T.as_tensor_variable(alpha), theano.config.floatX)
        self.beta1 = T.cast(T.as_tensor_variable(beta1), theano.config.floatX)
        self.beta2 = T.cast(T.as_tensor_variable(beta2), theano.config.floatX)
        self.epsilon = epsilon
        # self.m = [T.zeros(p.get_value().shape, dtype=theano.config.floatX) for p in parameters]
        # self.v = [T.zeros(p.get_value().shape, dtype=theano.config.floatX) for p in parameters]
        print('# ADAM. ALPHA = %s BETA1 = %s BETA2 = %s' % (alpha, beta1, beta2))

    def get_updates(self, params, grads):
        t_prev = theano.shared(np.float32(0.))
        updates = OrderedDict()

        # Using theano constant to prevent upcasting of float32
        one = T.constant(1)

        t = t_prev + 1
        a_t = self.alpha * T.sqrt(one - self.beta2 ** t) / (one - self.beta1 ** t)

        for param, g_t in zip(params, grads):
            value = param.get_value(borrow=True)
            m_prev = theano.shared(np.zeros(value.shape, dtype=value.dtype), broadcastable=param.broadcastable)
            v_prev = theano.shared(np.zeros(value.shape, dtype=value.dtype), broadcastable=param.broadcastable)

            m_t = self.beta1 * m_prev + (one - self.beta1) * g_t
            v_t = self.beta2 * v_prev + (one - self.beta2) * g_t ** 2
            step = a_t * m_t / (T.sqrt(v_t) + self.epsilon)

            updates[m_prev] = m_t
            updates[v_prev] = v_t
            updates[param] = param - step

        updates[t_prev] = t
        # t = T.cast(step, theano.config.floatX)
        # self.m = [self.beta1 * m_i + (1. - self.beta1) * grad_i for m_i, grad_i in zip(self.m, grad)]
        # self.v = [self.beta2 * v_i + (1. - self.beta2) * grad_i**2 for v_i, grad_i in zip(self.v, grad)]
        # m_hat = [1. / (1. - self.beta1 ** t) * m_i for m_i in self.m]
        # v_hat = [1. / (1. - self.beta2 ** t) * v_i for v_i in self.v]
        # delta = [T.cast(self.alpha * m_hat_i / (T.sqrt(v_hat_i) + 1e-8), theano.config.floatX)
        #          for m_hat_i, v_hat_i in zip(m_hat, v_hat)]
        return updates


class AdaMax(object):
    def __init__(self, alpha=2e-3, beta1=0.9, beta2=0.999, epsilon=1e-8):
        self.alpha = T.cast(T.as_tensor_variable(alpha), theano.config.floatX)
        self.beta1 = T.cast(T.as_tensor_variable(beta1), theano.config.floatX)
        self.beta2 = T.cast(T.as_tensor_variable(beta2), theano.config.floatX)
        self.epsilon = T.cast(T.as_tensor_variable(epsilon), theano.config.floatX)
        # self.m = [T.zeros(p.get_value().shape, dtype=theano.config.floatX) for p in parameters]
        # self.u = T.cast(T.as_tensor_variable(0.), theano.config.floatX)
        print('# ADAMAX. ALPHA = %s BETA1 = %s BETA2 = %s' % (alpha, beta1, beta2))

    def get_updates(self, params, grads):
        # self.m = [self.beta1 * m_i + (1 - self.beta1) * grad_i for m_i, grad_i in zip(self.m, grad)]
        # self.u = T.maximum(self.u, max([T.abs_(grad_i).sum() for grad_i in grad]))
        # delta = [T.cast(self.alpha / (1 - self.beta1 ** t) * m_i / self.u, theano.config.floatX)
        #          for m_i in self.m]
        t_prev = theano.shared(np.float32(0.))
        updates = OrderedDict()

        # Using theano constant to prevent upcasting of float32
        one = T.constant(1)

        t = t_prev + 1
        a_t = self.alpha / (one - self.beta1 ** t)

        for param, g_t in zip(params, grads):
            value = param.get_value(borrow=True)
            m_prev = theano.shared(np.zeros(value.shape, dtype=value.dtype),
                                   broadcastable=param.broadcastable)
            u_prev = theano.shared(np.zeros(value.shape, dtype=value.dtype),
                                   broadcastable=param.broadcastable)

            m_t = self.beta1 * m_prev + (one - self.beta1) * g_t
            u_t = T.maximum(self.beta2 * u_prev, abs(g_t))
            step = a_t * m_t / (u_t + self.epsilon)

            updates[m_prev] = m_t
            updates[u_prev] = u_t
            updates[param] = param - step

        updates[t_prev] = t
        return updates
