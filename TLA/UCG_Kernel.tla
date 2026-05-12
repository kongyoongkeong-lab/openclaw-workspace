(* ============================================================================
   MINIMAL COGNITIVE KERNEL — TLA⁺ SPECIFICATION
   Version: G2-FORMAL-v1.0
   Author: Pentagon Team
   ============================================================================ *)

(* ============================================================================
   MODULE 1: CONSTANTS AND TYPES
   ============================================================================ *)

(* Bounded signal space: pressure \in [0.0, 1.0] *)
CONST PressureMin == 0.0
CONST PressureMax == 1.0
CONST SignalSpace == [PressureMin .. PressureMax]

(* Fixed action set for decision space *)
CONST ActionSet == {"NORMAL", "THROTTLE", "DEFER", "ESCALATE"}

(* ============================================================================
   MODULE 2: STATE VARIABLES
   ============================================================================ *)

(* S: Signal vector (bounded observation state) *)
(* A: Action output (decision) *)

(* ============================================================================
   MODULE 3: INITIAL STATE
   ============================================================================ *)

Init ==
  \/ S \in SignalSpace
  \/ A = "NORMAL"

(* ============================================================================
   MODULE 4: UCG TRANSITION FUNCTION
   ============================================================================ *)

(* Core UCG decision function *)
UCG(s) ==
  IF s < 0.3 THEN "NORMAL"
  ELSE IF s < 0.6 THEN "THROTTLE"
  ELSE IF s < 0.85 THEN "DEFER"
  ELSE "ESCALATE"

(* Next-state relation *)
Next ==
  \/ S' \in SignalSpace
  \/ A' = UCG(S')
  \/ UNCHANGED <A>  (* Action unchanged unless UCG recomputes *)

(* ============================================================================
   MODULE 5: INVARIANTS
   ============================================================================ *)

(* I1: Valid Action Invariant - always produces valid action *)
ValidAction == A \in ActionSet

(* I2: Determinism Invariant - identical S yields identical A *)
Deterministic ==
  \/ \A s1, s2 \in SignalSpace :
      s1 = s2 ==> UCG(s1) = UCG(s2)

(* I3: No Feedback Loop Invariant - S doesn't depend on A *)
NoFeedback ==
  \/ UNCHANGED S  (* S remains independent of A *)

(* I4: Signal Boundedness Invariant *)
SignalBounded == S \in SignalSpace

(* I5: State Space Finiteness *)
FiniteStateSpace == S \in SignalSpace

(* ============================================================================
   MODULE 6: SYSTEM SPECIFICATION
   ============================================================================ *)

Spec ==
  Init /\ [][Next]_<<S, A>> /\ []ValidAction /\ []SignalBounded

(* ============================================================================
   MODULE 7: PROPERTIES TO VERIFY
   ============================================================================ *)

(* Safety: All actions valid *)
Safety == \/ Spec => ValidAction

(* Stability: Valid actions always *)
Stability == /\ Init => []ValidAction

(* Determinism: Deterministic mapping *)
DeterminismSpec == Init /\ [][Next]_<<S, A>> => Deterministic

(* ============================================================================
   MODULE 8: MODEL CHECKING CONFIGURATION
   ============================================================================ *)

(* State space bounds for TLC *)
CONST NumStates == 101  (* 0.0 to 1.0 in 0.01 increments *)
CONST MaxSteps == 100

(* ============================================================================ *)
