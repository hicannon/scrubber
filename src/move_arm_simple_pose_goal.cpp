#include <ros/ros.h>
#include <actionlib/client/simple_action_client.h>

#include <arm_navigation_msgs/MoveArmAction.h>
#include <arm_navigation_msgs/utils.h>

arm_navigation_msgs::MoveArmGoal getGoal(double x, double y, double z,
              double ox, double oy, double oz, double ow, bool rightArm) {
  arm_navigation_msgs::MoveArmGoal goal;
  
  if (rightArm)
	goal.motion_plan_request.group_name = "right_arm";
  else
  	goal.motion_plan_request.group_name = "left_arm";
  goal.motion_plan_request.num_planning_attempts = 1;
  goal.motion_plan_request.planner_id = std::string("");
  goal.planner_service_name = std::string("ompl_planning/plan_kinematic_path");
  goal.motion_plan_request.allowed_planning_time = ros::Duration(60.0);

  arm_navigation_msgs::SimplePoseConstraint desired_pose;
  desired_pose.header.frame_id = "base_link";
  if (rightArm)
	desired_pose.link_name = "r_wrist_roll_link";
  else
  	desired_pose.link_name = "l_wrist_roll_link";
  desired_pose.pose.position.x = x;
  desired_pose.pose.position.y = y;
  desired_pose.pose.position.z = z;

  desired_pose.pose.orientation.x = ox;
  desired_pose.pose.orientation.y = oy;
  desired_pose.pose.orientation.z = oz;
  desired_pose.pose.orientation.w = ow;

  desired_pose.absolute_position_tolerance.x = 0.02;
  desired_pose.absolute_position_tolerance.y = 0.02;
  desired_pose.absolute_position_tolerance.z = 0.02;

  desired_pose.absolute_roll_tolerance = 0.04;
  desired_pose.absolute_pitch_tolerance = 0.04;
  desired_pose.absolute_yaw_tolerance = 0.04;
  
  arm_navigation_msgs::addGoalConstraintToMoveArmGoal(desired_pose,goal);

  return goal;
}

void actualizeGoal(ros::NodeHandle& nh,
                   actionlib::SimpleActionClient<arm_navigation_msgs::MoveArmAction>& client,
                   arm_navigation_msgs::MoveArmGoal goal) {
  if (nh.ok())
  {
    bool finished_within_time = false;
    client.sendGoal(goal);
    finished_within_time = client.waitForResult(ros::Duration(200.0));
    if (!finished_within_time)
    {
      client.cancelGoal();
      ROS_INFO("Timed out achieving goal");
    }
    else
    {
      actionlib::SimpleClientGoalState state = client.getState();
      bool success = (state == actionlib::SimpleClientGoalState::SUCCEEDED);
      if(success)
        ROS_INFO("Action finished: %s",state.toString().c_str());
      else
        ROS_INFO("Action failed: %s",state.toString().c_str());
    }
  } 
}

int main(int argc, char **argv){
  ros::init (argc, argv, "move_arm_pose_goal");
  ros::NodeHandle nh;
  actionlib::SimpleActionClient<arm_navigation_msgs::MoveArmAction> move_rarm("move_right_arm",true);
  actionlib::SimpleActionClient<arm_navigation_msgs::MoveArmAction> move_larm("move_left_arm",true);
  ROS_INFO("Connecting to server...");
  move_rarm.waitForServer();
  move_larm.waitForServer();
  ROS_INFO("Connected to server");
 
  actualizeGoal(nh, move_rarm, getGoal(0,-0.7,1.2,0,0,0,1, true));
  actualizeGoal(nh, move_rarm, getGoal(0.75,-0.2,0.8,0,0,0,1, true));
  actualizeGoal(nh, move_rarm, getGoal(0.5,-0.35,0.35,0,0,0,1, true));

  ros::shutdown();
}
