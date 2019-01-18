"""LTLMoP sensor handler for pragbot."""

# Copyright (C) 2013 Constantine Lignos
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


class sensorHandler(object):
    """Report the robot's current sensor status."""

    def __init__(self, proj, shared_data):  # pylint: disable=W0613

        self._name = type(self).__name__

        # Store reference to proj
        self._proj = proj

        # Store reference to server proxy
        self._proxy = \
            proj.h_instance['init'][proj.currentConfig.main_robot].getSharedData()["proxy"]

        self.sensors = {"bomb": self.bomb, "defuse_done": self.defuse_done}
        self.defuse_done_status = False

    def get_sensor(self, sensor_name, initial=False):
        """Report whether we currently see a fiducial of the requested type.

        sensor_name (string): The type of the fiducial to query.
        """
        if initial:
            # Nothing to do on initialization
            return True
        else:
            # TODO: Implement this to match what the pragbot system
            # expects. No idea whether this line reflects the current
            # implementation. Commented out for now. Another line used
            # self._proxy.receiveHandlerMessages("Find Bomb",
            # sensor_name). Take a look at the pragbot game code to
            # figure out what it should be.
            # return self._proxy.receiveHandlerMessages(sensor_name, current_region)
            if sensor_name in self.sensors:
                return self.sensors[sensor_name]()
            return False

    def bomb(self):
        """Report the state of the bomb sensor by pinging pragbot client."""
        location_string = self._proxy.receiveHandlerMessages("Sensor", "bomb")
        pieces = location_string.split(",")
        numbombs = int(pieces[0])
        if numbombs > 0:
            return True
        return False

    def defuse_done(self):
        """Report whether defuse is done."""
        return self.defuse_done_status

    def set_action_done(self, action_name, value):
        """Set whether an action is done to the given value."""
        if action_name == "defuse":
            self.defuse_done_status = value
